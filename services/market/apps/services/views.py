from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.db.models import Q
from .models import Service, Deal, Transaction
from .serializers import (
    ServiceSerializer, 
    DealSerializer, 
    ProposeDealSerializer,
    TransactionSerializer
)
from .services import AIService
from .deal_service import DealService


class ServiceViewSet(viewsets.ModelViewSet):
    """Управление услугами"""
    queryset = Service.objects.all()
    serializer_class = ServiceSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_queryset(self):
        queryset = Service.objects.all().order_by('-created_at')
        
        owner_id = self.request.query_params.get('owner_id')
        if owner_id:
            queryset = queryset.filter(owner_id=owner_id)

        cats_param = self.request.query_params.get('categories') or self.request.query_params.get('category')
        if cats_param:
            cat_list = cats_param.split(',')
            queryset = queryset.filter(category__in=cat_list)

        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) | 
                Q(description__icontains=search) |
                Q(tags__contains=[search])
            )

        return queryset

    def list(self, request):
        services = self.get_queryset()
        serializer = self.get_serializer(services, many=True)
        return Response({'status': 'success', 'data': serializer.data, 'error': None})

    def retrieve(self, request, pk=None):
        try:
            service = self.get_object()
            serializer = self.get_serializer(service)
            return Response({'status': 'success', 'data': serializer.data, 'error': None})
        except Service.DoesNotExist:
            return Response({'status': 'error', 'error': 'Услуга не найдена', 'data': None}, status=404)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response({'status': 'error', 'error': serializer.errors, 'data': None}, status=400)

        serializer.save(
            owner_id=request.user.id,
            owner_name=request.data.get('owner_name', 'Фрилансер'),
            owner_avatar=request.data.get('owner_avatar', '')
        )
        return Response({'status': 'success', 'data': serializer.data, 'error': None}, status=201)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        if str(instance.owner_id) != str(request.user.id):
            return Response({'status': 'error', 'error': 'Нет прав', 'data': None}, status=403)

        serializer = self.get_serializer(instance, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response({'status': 'error', 'error': serializer.errors, 'data': None}, status=400)

        serializer.save()
        return Response({'status': 'success', 'data': serializer.data, 'error': None})

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if str(instance.owner_id) != str(request.user.id):
            return Response({'status': 'error', 'error': 'Нет прав', 'data': None}, status=403)

        instance.delete()
        return Response({'status': 'success', 'data': {'message': 'Услуга удалена'}, 'error': None})


class DealViewSet(viewsets.ViewSet):
    """
    ✅ УЛУЧШЕННОЕ API ДЛЯ РАБОТЫ С ЗАКАЗАМИ
    Новая четкая логика как на Avito/Fiverr
    """
    permission_classes = [IsAuthenticated]

    def list(self, request):
        """Получить все заказы пользователя"""
        user_id = request.user.id
        deals = Deal.objects.filter(
            Q(client_id=user_id) | Q(worker_id=user_id)
        ).order_by('-created_at')

        serializer = DealSerializer(deals, many=True)
        return Response({'status': 'success', 'data': serializer.data, 'error': None})

    def retrieve(self, request, pk=None):
        """Получить конкретный заказ"""
        try:
            deal = Deal.objects.get(id=pk)
            user_id = str(request.user.id)

            if user_id not in [str(deal.client_id), str(deal.worker_id)]:
                return Response({'error': 'Нет прав'}, status=403)

            serializer = DealSerializer(deal)
            return Response({'status': 'success', 'data': serializer.data})
        except Deal.DoesNotExist:
            return Response({'error': 'Заказ не найден'}, status=404)

    @action(detail=False, methods=['get'], url_path='by-chat/(?P<chat_room_id>[^/.]+)')
    def by_chat(self, request, chat_room_id=None):
        """Получить заказ для конкретного чата"""
        try:
            deal = Deal.objects.get(chat_room_id=chat_room_id)
            user_id = str(request.user.id)

            if user_id not in [str(deal.client_id), str(deal.worker_id)]:
                return Response({'error': 'Нет прав'}, status=403)

            serializer = DealSerializer(deal)
            return Response({'status': 'success', 'data': serializer.data})
        except Deal.DoesNotExist:
            return Response({'status': 'success', 'data': None})

    # ============================================================
    # ✅ НОВЫЕ ENDPOINTS С УЛУЧШЕННОЙ ЛОГИКОЙ
    # ============================================================

    @action(detail=False, methods=['post'], url_path='propose')
    def propose(self, request):
        """
        Предложить условия заказа.
        Можно менять только ДО оплаты.
        """
        chat_room_id = request.data.get('chat_room_id')
        if not chat_room_id:
            return Response({'error': 'chat_room_id обязателен'}, status=400)

        serializer = ProposeDealSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({'error': serializer.errors}, status=400)

        try:
            import requests as req
            auth_header = request.headers.get('Authorization', '')
            token = auth_header.split(' ')[1] if auth_header.startswith('Bearer ') else ''

            # Получаем данные чата
            chat_url = f"http://localhost:8003/api/chat/rooms/{chat_room_id}/"
            chat_response = req.get(chat_url, headers={'Authorization': f'Bearer {token}'})
            
            if chat_response.status_code != 200:
                return Response({'error': 'Не удалось получить данные чата'}, status=400)
            
            chat_data = chat_response.json()
            members = chat_data['data']['members']

            proposer_id = str(request.user.id)
            proposer_role = request.user.role
            other_member = [m for m in members if str(m) != proposer_id][0]
            
            # Определяем роли
            try:
                deal = Deal.objects.get(chat_room_id=chat_room_id)
                client_id = deal.client_id
                worker_id = deal.worker_id
            except Deal.DoesNotExist:
                if proposer_role == 'client':
                    client_id = proposer_id
                    worker_id = other_member
                else:
                    worker_id = proposer_id
                    client_id = other_member
            
            # Создаем или получаем заказ
            deal = DealService.get_or_create_deal(
                chat_room_id=chat_room_id,
                client_id=client_id,
                worker_id=worker_id
            )
            
            # Предлагаем условия
            deal = DealService.propose_terms(
                deal=deal,
                proposer_id=proposer_id,
                title=serializer.validated_data['title'],
                description=serializer.validated_data['description'],
                price=serializer.validated_data['price'],
                auth_token=token
            )
            
            return Response({
                'status': 'success',
                'data': DealSerializer(deal).data,
                'message': 'Условия предложены. Ожидаем согласия второй стороны.'
            })
            
        except Exception as e:
            return Response({'error': str(e)}, status=400)
    
    @action(detail=True, methods=['post'], url_path='agree')
    def agree(self, request, pk=None):
        """✅ Согласиться с условиями"""
        try:
            deal = Deal.objects.get(id=pk)
            user_id = str(request.user.id)

            if user_id not in [str(deal.client_id), str(deal.worker_id)]:
                return Response({'error': 'Нет прав'}, status=403)
            
            auth_header = request.headers.get('Authorization', '')
            token = auth_header.split(' ')[1] if auth_header.startswith('Bearer ') else ''
            
            deal = DealService.agree_terms(deal, user_id, token)
            
            message = 'Обе стороны согласны! Можно оплачивать.' if deal.client_agreed and deal.worker_agreed else 'Вы приняли условия.'
            
            return Response({
                'status': 'success',
                'data': DealSerializer(deal).data,
                'message': message
            })
            
        except Deal.DoesNotExist:
            return Response({'error': 'Заказ не найден'}, status=404)
        except Exception as e:
            return Response({'error': str(e)}, status=400)
    
    @action(detail=True, methods=['post'], url_path='pay')
    def pay(self, request, pk=None):
        """💳 Оплатить заказ (только клиент)"""
        try:
            deal = Deal.objects.get(id=pk)
            user_id = str(request.user.id)
            
            auth_header = request.headers.get('Authorization', '')
            token = auth_header.split(' ')[1] if auth_header.startswith('Bearer ') else ''
            
            deal = DealService.pay_and_start(deal, user_id, token)
            
            return Response({
                'status': 'success',
                'data': DealSerializer(deal).data,
                'message': 'Заказ оплачен! Средства захолдированы. Исполнитель может начинать работу.'
            })
            
        except Deal.DoesNotExist:
            return Response({'error': 'Заказ не найден'}, status=404)
        except Exception as e:
            return Response({'error': str(e)}, status=400)
    
    @action(detail=True, methods=['post'], url_path='deliver')
    def deliver(self, request, pk=None):
        """📦 Сдать работу (только воркер)"""
        try:
            deal = Deal.objects.get(id=pk)
            user_id = str(request.user.id)
            delivery_message = request.data.get('delivery_message', '')
            
            auth_header = request.headers.get('Authorization', '')
            token = auth_header.split(' ')[1] if auth_header.startswith('Bearer ') else ''
            
            deal = DealService.deliver_work(deal, user_id, delivery_message, token)
            
            return Response({
                'status': 'success',
                'data': DealSerializer(deal).data,
                'message': 'Работа сдана на проверку!'
            })
            
        except Deal.DoesNotExist:
            return Response({'error': 'Заказ не найден'}, status=404)
        except Exception as e:
            return Response({'error': str(e)}, status=400)
    
    @action(detail=True, methods=['post'], url_path='revision')
    def revision(self, request, pk=None):
        """🔄 Запросить доработку (только клиент)"""
        try:
            deal = Deal.objects.get(id=pk)
            user_id = str(request.user.id)
            revision_reason = request.data.get('revision_reason', '')
            
            auth_header = request.headers.get('Authorization', '')
            token = auth_header.split(' ')[1] if auth_header.startswith('Bearer ') else ''
            
            deal = DealService.request_revision(deal, user_id, revision_reason, token)
            
            return Response({
                'status': 'success',
                'data': DealSerializer(deal).data,
                'message': f'Доработка запрошена ({deal.revision_count}/{deal.max_revisions})'
            })
            
        except Deal.DoesNotExist:
            return Response({'error': 'Заказ не найден'}, status=404)
        except Exception as e:
            return Response({'error': str(e)}, status=400)
    
    @action(detail=True, methods=['post'], url_path='complete')
    def complete(self, request, pk=None):
        """🎉 Принять работу и завершить (только клиент)"""
        try:
            deal = Deal.objects.get(id=pk)
            user_id = str(request.user.id)
            completion_message = request.data.get('completion_message', 'Спасибо!')
            
            auth_header = request.headers.get('Authorization', '')
            token = auth_header.split(' ')[1] if auth_header.startswith('Bearer ') else ''
            
            deal = DealService.complete_deal(deal, user_id, completion_message, token)
            
            return Response({
                'status': 'success',
                'data': DealSerializer(deal).data,
                'message': 'Заказ завершен! Деньги переведены исполнителю.'
            })
            
        except Deal.DoesNotExist:
            return Response({'error': 'Заказ не найден'}, status=404)
        except Exception as e:
            return Response({'error': str(e)}, status=400)
    
    @action(detail=True, methods=['post'], url_path='cancel')
    def cancel(self, request, pk=None):
        """❌ Отменить заказ"""
        try:
            deal = Deal.objects.get(id=pk)
            user_id = str(request.user.id)
            reason = request.data.get('reason', 'Не указана')
            
            auth_header = request.headers.get('Authorization', '')
            token = auth_header.split(' ')[1] if auth_header.startswith('Bearer ') else ''
            
            deal = DealService.cancel_deal(deal, user_id, reason, token)
            
            message = 'Заказ отменен'
            if deal.payment_completed:
                message += '. Средства возвращены клиенту.'
            
            return Response({
                'status': 'success',
                'data': DealSerializer(deal).data,
                'message': message
            })
            
        except Deal.DoesNotExist:
            return Response({'error': 'Заказ не найден'}, status=404)
        except Exception as e:
            return Response({'error': str(e)}, status=400)
    
    @action(detail=False, methods=['post'], url_path='generate-tz')
    def generate_tz(self, request):
        """AI-генерация ТЗ"""
        service_id = request.data.get('service_id')
        raw_requirements = request.data.get('raw_requirements')
        
        if not service_id or not raw_requirements:
            return Response({'error': 'service_id и raw_requirements обязательны'}, status=400)
        
        try:
            generated_tz = AIService.generate_tz(service_id, raw_requirements)
            
            return Response({
                'status': 'success',
                'data': {'generated_tz': generated_tz}
            })

        except Exception as e:
            return Response({'error': str(e)}, status=400)
