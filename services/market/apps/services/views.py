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
    CancelDealSerializer,
    GenerateTZSerializer,
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
        
        # Фильтрация по владельцу
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

        return Response({
            'status': 'success',
            'data': serializer.data,
            'error': None
        })

    def retrieve(self, request, pk=None):
        try:
            service = self.get_object()
            serializer = self.get_serializer(service)

            return Response({
                'status': 'success',
                'data': serializer.data,
                'error': None
            })
        except Service.DoesNotExist:
            return Response({
                'status': 'error',
                'error': 'Услуга не найдена',
                'data': None
            }, status=status.HTTP_404_NOT_FOUND)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        if not serializer.is_valid():
            return Response({
                'status': 'error',
                'error': serializer.errors,
                'data': None
            }, status=status.HTTP_400_BAD_REQUEST)

        serializer.save(
            owner_id=request.user.id,
            owner_name=request.data.get('owner_name', 'Фрилансер'),
            owner_avatar=request.data.get('owner_avatar', '')
        )

        return Response({
            'status': 'success',
            'data': serializer.data,
            'error': None
        }, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()

        if str(instance.owner_id) != str(request.user.id):
            return Response({
                'status': 'error',
                'error': 'Вы не можете редактировать чужую услугу',
                'data': None
            }, status=status.HTTP_403_FORBIDDEN)

        serializer = self.get_serializer(instance, data=request.data, partial=True)

        if not serializer.is_valid():
            return Response({
                'status': 'error',
                'error': serializer.errors,
                'data': None
            }, status=status.HTTP_400_BAD_REQUEST)

        serializer.save()

        return Response({
            'status': 'success',
            'data': serializer.data,
            'error': None
        })

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()

        if str(instance.owner_id) != str(request.user.id):
            return Response({
                'status': 'error',
                'error': 'Вы не можете удалить чужую услугу',
                'data': None
            }, status=status.HTTP_403_FORBIDDEN)

        instance.delete()

        return Response({
            'status': 'success',
            'data': {'message': 'Услуга успешно удалена'},
            'error': None
        })

    @action(detail=False, methods=['get'], url_path='categories')
    def categories(self, request):
        """Получить список всех категорий с количеством услуг"""
        from django.db.models import Count
        
        categories = Service.objects.values('category').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # Добавляем человекочитаемые названия
        category_dict = dict(Service.CATEGORY_CHOICES)
        result = [
            {
                'value': cat['category'],
                'label': category_dict.get(cat['category'], cat['category']),
                'count': cat['count']
            }
            for cat in categories
        ]
        
        return Response({
            'status': 'success',
            'data': result,
            'error': None
        })


class DealViewSet(viewsets.ViewSet):
    """Управление сделками"""
    permission_classes = [IsAuthenticated]

    def list(self, request):
        """Получить все сделки пользователя (история)"""
        user_id = request.user.id
        deals = Deal.objects.filter(
            Q(client_id=user_id) | Q(worker_id=user_id)
        ).order_by('-created_at')

        serializer = DealSerializer(deals, many=True)

        return Response({
            'status': 'success',
            'data': serializer.data,
            'error': None
        })

    def retrieve(self, request, pk=None):
        """Получить конкретную сделку"""
        try:
            deal = Deal.objects.get(id=pk)
            user_id = str(request.user.id)

            if user_id not in [str(deal.client_id), str(deal.worker_id)]:
                return Response({'error': 'Нет прав'}, status=403)

            serializer = DealSerializer(deal)
            return Response({
                'status': 'success',
                'data': serializer.data
            })
        except Deal.DoesNotExist:
            return Response({'error': 'Сделка не найдена'}, status=404)

    @action(detail=False, methods=['get'], url_path='by-chat/(?P<chat_room_id>[^/.]+)')
    def by_chat(self, request, chat_room_id=None):
        """Получить сделку для конкретного чата"""
        try:
            deal = Deal.objects.get(chat_room_id=chat_room_id)
            user_id = str(request.user.id)

            if user_id not in [str(deal.client_id), str(deal.worker_id)]:
                return Response({'error': 'Нет прав'}, status=403)

            serializer = DealSerializer(deal)
            return Response({
                'status': 'success',
                'data': serializer.data
            })
        except Deal.DoesNotExist:
            return Response({
                'status': 'success',
                'data': None
            })

    @action(detail=False, methods=['post'], url_path='propose')
    def propose(self, request):
        """
        Предложить условия сделки.
        Требует: chat_room_id, title, description, price
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

            chat_url = f"http://localhost:8003/api/chat/rooms/{chat_room_id}/"
            chat_response = req.get(chat_url, headers={'Authorization': f'Bearer {token}'})
            
            if chat_response.status_code != 200:
                return Response({'error': 'Не удалось получить данные чата'}, status=400)
            
            chat_data = chat_response.json()
            members = chat_data['data']['members']

            proposer_id = str(request.user.id)
            proposer_role = request.user.role  # 'client' или 'worker'
            other_member = [m for m in members if str(m) != proposer_id][0]
            
            # Проверяем есть ли уже сделка для этого чата
            try:
                deal = Deal.objects.get(chat_room_id=chat_room_id)
                # Если сделка уже есть, роли уже определены
                client_id = deal.client_id
                worker_id = deal.worker_id
            except Deal.DoesNotExist:
                # Новая сделка - определяем роли по полю role пользователя
                if proposer_role == 'client':
                    # Клиент предлагает -> он клиент, другой воркер
                    client_id = proposer_id
                    worker_id = other_member
                else:
                    # Воркер предлагает -> он воркер, другой клиент
                    worker_id = proposer_id
                    client_id = other_member
            
            deal = DealService.get_or_create_deal_for_chat(
                chat_room_id=chat_room_id,
                client_id=client_id,
                worker_id=worker_id
            )
            
            # Предлагаем условия
            deal = DealService.propose_deal(
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
                'message': 'Предложение отправлено второй стороне'
            })
            
        except Exception as e:
            return Response({'error': str(e)}, status=400)
    
    @action(detail=True, methods=['post'], url_path='confirm')
    def confirm(self, request, pk=None):
        """Подтвердить предложенную сделку"""
        try:
            deal = Deal.objects.get(id=pk)
            user_id = str(request.user.id)

            if user_id not in [str(deal.client_id), str(deal.worker_id)]:
                return Response({'error': 'Нет прав'}, status=403)

            if str(deal.proposed_by) == user_id:
                return Response({'error': 'Вы уже подтвердили (вы предложили)'}, status=400)
            
            auth_header = request.headers.get('Authorization', '')
            token = auth_header.split(' ')[1] if auth_header.startswith('Bearer ') else ''
            
            deal = DealService.confirm_deal(deal, user_id, token)
            
            if deal.status == 'active':
                message = 'Сделка активирована! Средства захолдированы.'
            else:
                message = 'Вы подтвердили условия. Ожидаем второй стороны.'
            
            return Response({
                'status': 'success',
                'data': DealSerializer(deal).data,
                'message': message
            })
            
        except Deal.DoesNotExist:
            return Response({'error': 'Сделка не найдена'}, status=404)
        except Exception as e:
            return Response({'error': str(e)}, status=400)
    
    @action(detail=True, methods=['post'], url_path='request-completion')
    def request_completion(self, request, pk=None):
        """Запросить завершение"""
        try:
            deal = Deal.objects.get(id=pk)
            user_id = str(request.user.id)
            
            if user_id not in [str(deal.client_id), str(deal.worker_id)]:
                return Response({'error': 'Нет прав'}, status=403)
            
            auth_header = request.headers.get('Authorization', '')
            token = auth_header.split(' ')[1] if auth_header.startswith('Bearer ') else ''
            
            deal = DealService.request_completion(deal, user_id, token)
            
            return Response({
                'status': 'success',
                'data': DealSerializer(deal).data,
                'message': 'Запрос на завершение отправлен'
            })
            
        except Deal.DoesNotExist:
            return Response({'error': 'Сделка не найдена'}, status=404)
        except Exception as e:
            return Response({'error': str(e)}, status=400)
    
    @action(detail=True, methods=['post'], url_path='complete')
    def complete(self, request, pk=None):
        """Завершить сделку"""
        try:
            deal = Deal.objects.get(id=pk)
            user_id = str(request.user.id)
            
            if user_id not in [str(deal.client_id), str(deal.worker_id)]:
                return Response({'error': 'Нет прав'}, status=403)
            
            auth_header = request.headers.get('Authorization', '')
            token = auth_header.split(' ')[1] if auth_header.startswith('Bearer ') else ''
            
            deal = DealService.complete_deal(deal, user_id, token)
            
            return Response({
                'status': 'success',
                'data': DealSerializer(deal).data,
                'message': 'Сделка завершена! Средства переведены исполнителю.'
            })
            
        except Deal.DoesNotExist:
            return Response({'error': 'Сделка не найдена'}, status=404)
        except Exception as e:
            return Response({'error': str(e)}, status=400)
    
    @action(detail=True, methods=['post'], url_path='cancel')
    def cancel(self, request, pk=None):
        """Отменить сделку"""
        try:
            deal = Deal.objects.get(id=pk)
            user_id = str(request.user.id)
            
            if user_id not in [str(deal.client_id), str(deal.worker_id)]:
                return Response({'error': 'Нет прав'}, status=403)
            
            serializer = CancelDealSerializer(data=request.data)
            if not serializer.is_valid():
                return Response({'error': serializer.errors}, status=400)
            
            auth_header = request.headers.get('Authorization', '')
            token = auth_header.split(' ')[1] if auth_header.startswith('Bearer ') else ''
            
            deal = DealService.cancel_deal(
                deal, 
                user_id, 
                serializer.validated_data['reason'],
                token
            )
            
            return Response({
                'status': 'success',
                'data': DealSerializer(deal).data,
                'message': 'Сделка отменена'
            })
            
        except Deal.DoesNotExist:
            return Response({'error': 'Сделка не найдена'}, status=404)
        except Exception as e:
            return Response({'error': str(e)}, status=400)
    
    @action(detail=False, methods=['post'], url_path='generate-tz')
    def generate_tz(self, request):
        """AI-генерация ТЗ для сделки"""
        serializer = GenerateTZSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response({'error': serializer.errors}, status=400)
        
        try:
            generated_tz = AIService.generate_tz(
                service_id=serializer.validated_data['service_id'],
                client_requirements=serializer.validated_data['raw_requirements']
            )
            
            return Response({
                'status': 'success',
                'data': {
                    'generated_tz': generated_tz,
                    'message': 'ТЗ сгенерировано'
                }
            })

        except Exception as e:
            return Response({'error': str(e)}, status=400)
