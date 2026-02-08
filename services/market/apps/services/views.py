# services/market/apps/services/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.db.models import Q, Count, Avg
from django.db import transaction
from .models import Service, ServiceImage, Deal, Review, DealDeliveryAttachment, Favorite
from .serializers import (
    ServiceSerializer,
    ServiceImageSerializer,
    DealSerializer,
    ReviewSerializer,
    CreateDealSerializer,
    CompleteDealSerializer,
    FavoriteSerializer
)
from .throttling import AIGenerationThrottle, DealCreationThrottle, FileUploadThrottle, DealPaymentThrottle
from .services import AIService
from .deal_service import DealService
import os
import requests
import magic


class ServiceViewSet(viewsets.ModelViewSet):
    """Управление услугами"""
    queryset = Service.objects.all()
    serializer_class = ServiceSerializer
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'get_subcategories']:
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_queryset(self):
        queryset = Service.objects.all()
        
        if self.action == 'list':
            owner_id = self.request.query_params.get('owner_id')
            
            if owner_id:
                queryset = queryset.filter(owner_id=owner_id)
                
                if not self.request.user.is_authenticated or str(self.request.user.id) != str(owner_id):
                    queryset = queryset.filter(is_active=True)
            else:
                queryset = queryset.filter(is_active=True)

        # Фильтрация по категориям
        cats_param = self.request.query_params.get('categories') or self.request.query_params.get('category')
        if cats_param:
            cat_list = cats_param.split(',')
            queryset = queryset.filter(category__in=cat_list)
        
        # Фильтрация по подкатегориям
        subcats_param = self.request.query_params.get('subcategories') or self.request.query_params.get('subcategory')
        if subcats_param:
            subcat_list = subcats_param.split(',')
            queryset = queryset.filter(subcategory__in=subcat_list)

        # Поиск
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) | 
                Q(description__icontains=search) |
                Q(tags__contains=[search])
            )

        # Сортировка
        sort_by = self.request.query_params.get('sort', '-created_at')
        
        if sort_by == 'price_asc':
            queryset = queryset.order_by('price')
        elif sort_by == 'price_desc':
            queryset = queryset.order_by('-price')
        elif sort_by == 'popular':
            # Сортировка по популярности (количество избранного)
            queryset = queryset.annotate(
                favorites_count=Count('favorited_by')
            ).order_by('-favorites_count', '-created_at')
        elif sort_by == 'rating':
            # Сортировка по рейтингу владельца
            queryset = queryset.annotate(
                avg_rating=Avg('owner_id')  # Требует дополнительной логики
            ).order_by('-created_at')  # Временно по дате
        else:
            # По умолчанию - новые первые
            queryset = queryset.order_by('-created_at')

        return queryset

    def list(self, request):
        services = self.get_queryset()
        serializer = self.get_serializer(services, many=True)
        return Response({'status': 'success', 'data': serializer.data, 'error': None})

    def retrieve(self, request, pk=None):
        try:
            service = self.get_object()
            
            if not service.is_active:
                if not request.user.is_authenticated or str(request.user.id) != str(service.owner_id):
                    return Response({
                        'status': 'error', 
                        'error': 'Это объявление неактивно', 
                        'data': None
                    }, status=403)
            
            serializer = self.get_serializer(service)
            return Response({'status': 'success', 'data': serializer.data, 'error': None})
        except Service.DoesNotExist:
            return Response({'status': 'error', 'error': 'Услуга не найдена', 'data': None}, status=404)

    @action(detail=False, methods=['get'], url_path='subcategories')
    def get_subcategories(self, request):
        """Получить список всех подкатегорий для всех категорий"""
        subcategories_data = {}
        
        for category_value, category_label in Service.CATEGORY_CHOICES:
            subcats = Service.SUBCATEGORY_CHOICES.get(category_value, [])
            subcategories_data[category_value] = [
                {'value': subcat[0], 'label': subcat[1]} 
                for subcat in subcats
            ]
        
        return Response({
            'status': 'success',
            'data': subcategories_data,
            'error': None
        })

    def _validate_image_file(self, image_file):
        """Валидация изображения с MIME-type проверкой"""
        if image_file.size > 5 * 1024 * 1024:
            raise ValueError('Размер файла превышает 5MB')
        
        ext = os.path.splitext(image_file.name)[1][1:].lower()
        allowed_extensions = ['jpg', 'jpeg', 'png', 'gif', 'webp']
        
        if ext not in allowed_extensions:
            raise ValueError(f'Недопустимое расширение: {ext}')
        
        # MIME-type проверка
        file_head = image_file.read(2048)
        image_file.seek(0)
        
        mime = magic.from_buffer(file_head, mime=True)
        allowed_mimes = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
        
        if mime not in allowed_mimes:
            raise ValueError(f'Недопустимый MIME-type: {mime}')
        
        return True

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        """Создание нового объявления с проверкой подписки"""
        
        if request.user.role != 'worker':
            return Response({
                'status': 'error',
                'error': 'Создавать объявления могут только исполнители',
                'data': None
            }, status=403)
        
        is_active = False
        
        has_subscription = self._check_subscription(request.user.id)
        is_active = has_subscription
        
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response({'status': 'error', 'error': serializer.errors, 'data': None}, status=400)

        # Валидация подкатегории при создании
        category = serializer.validated_data.get('category')
        subcategory = serializer.validated_data.get('subcategory')
        
        if subcategory:
            valid_subcategories = [choice[0] for choice in Service.SUBCATEGORY_CHOICES.get(category, [])]
            if subcategory not in valid_subcategories:
                return Response({
                    'status': 'error',
                    'error': f'Недопустимая подкатегория для категории {category}',
                    'data': None
                }, status=400)

        service = serializer.save(
            owner_id=request.user.id,
            owner_name=request.data.get('owner_name', 'Фрилансер'),
            owner_avatar=request.data.get('owner_avatar', ''),
            is_active=is_active
        )
        
        # Валидация и сохранение изображений
        for i in range(5):
            image_key = f'image_{i}'
            if image_key in request.FILES:
                image_file = request.FILES[image_key]
                
                try:
                    self._validate_image_file(image_file)
                    
                    ServiceImage.objects.create(
                        service=service,
                        image=image_file,
                        order=i
                    )
                except ValueError as e:
                    # Пропускаем невалидные файлы
                    print(f"Ошибка валидации изображения {i}: {e}")
                    continue
        
        response_data = ServiceSerializer(service, context={'request': request}).data
        
        if not is_active:
            return Response({
                'status': 'success', 
                'data': response_data, 
                'error': None,
                'message': 'Объявление создано в неактивном статусе. Для публикации требуется активная подписка.'
            }, status=201)
        
        return Response({'status': 'success', 'data': response_data, 'error': None}, status=201)

    @transaction.atomic
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        if str(instance.owner_id) != str(request.user.id):
            return Response({'status': 'error', 'error': 'Нет прав', 'data': None}, status=403)

        final_is_active = instance.is_active
        
        if 'is_active' in request.data:
            requested_active = request.data.get('is_active')
            if isinstance(requested_active, str):
                requested_active = requested_active.lower() in ('true', '1', 'yes')
            
            if requested_active and request.user.role == 'worker':
                has_subscription = self._check_subscription(request.user.id)
                
                if not has_subscription:
                    return Response({
                        'status': 'error',
                        'error': 'Для активации объявления требуется активная подписка',
                        'data': None,
                        'require_subscription': True
                    }, status=403)
                
                final_is_active = True
            else:
                final_is_active = requested_active

        serializer = self.get_serializer(instance, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response({'status': 'error', 'error': serializer.errors, 'data': None}, status=400)

        # Валидация подкатегории при обновлении
        category = serializer.validated_data.get('category', instance.category)
        subcategory = serializer.validated_data.get('subcategory')
        
        if subcategory:
            valid_subcategories = [choice[0] for choice in Service.SUBCATEGORY_CHOICES.get(category, [])]
            if subcategory not in valid_subcategories:
                return Response({
                    'status': 'error',
                    'error': f'Недопустимая подкатегория для категории {category}',
                    'data': None
                }, status=400)

        service = serializer.save(is_active=final_is_active)
        
        # Валидация и обновление изображений
        for i in range(5):
            image_key = f'image_{i}'
            if image_key in request.FILES:
                image_file = request.FILES[image_key]
                
                try:
                    self._validate_image_file(image_file)
                    
                    ServiceImage.objects.filter(service=instance, order=i).delete()
                    
                    ServiceImage.objects.create(
                        service=service,
                        image=image_file,
                        order=i
                    )
                except ValueError as e:
                    print(f"Ошибка валидации изображения {i}: {e}")
                    continue

        return Response({'status': 'success', 'data': ServiceSerializer(service, context={'request': request}).data, 'error': None})

    @transaction.atomic
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if str(instance.owner_id) != str(request.user.id):
            return Response({'status': 'error', 'error': 'Нет прав', 'data': None}, status=403)

        instance.delete()
        return Response({'status': 'success', 'data': {'message': 'Услуга удалена'}, 'error': None})

    @action(detail=True, methods=['delete'], url_path='delete-image/(?P<image_id>[^/.]+)')
    def delete_image(self, request, pk=None, image_id=None):
        """Удалить конкретное изображение услуги"""
        try:
            service = self.get_object()
            if str(service.owner_id) != str(request.user.id):
                return Response({'status': 'error', 'error': 'Нет прав'}, status=403)
            
            image = ServiceImage.objects.get(id=image_id, service=service)
            image.delete()
            
            return Response({'status': 'success', 'message': 'Изображение удалено'})
        except ServiceImage.DoesNotExist:
            return Response({'status': 'error', 'error': 'Изображение не найдено'}, status=404)

    @action(detail=False, methods=['post'], url_path='deactivate-all')
    def deactivate_all(self, request):
        """Деактивировать все объявления воркера (вызывается при истечении подписки)"""
        if request.user.role != 'worker':
            return Response({'status': 'error', 'error': 'Только для воркеров'}, status=403)

        count = Service.objects.filter(
            owner_id=request.user.id,
            is_active=True
        ).update(is_active=False)

        return Response({
            'status': 'success',
            'data': {'deactivated_count': count},
            'message': f'Деактивировано объявлений: {count}'
        })

    def _check_subscription(self, user_id):
        """Проверка активной подписки через Auth Service"""
        try:
            auth_header = self.request.headers.get('Authorization', '')
            token = auth_header.split(' ')[1] if auth_header.startswith('Bearer ') else ''
            
            subscription_url = 'http://localhost:8001/api/auth/subscription/'
            
            response = requests.get(
                subscription_url,
                headers={'Authorization': f'Bearer {token}'},
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                subscription_is_active = data.get('data', {}).get('is_active', False)
                return bool(subscription_is_active)
            
            return False
            
        except Exception:
            return False


class FavoriteViewSet(viewsets.ViewSet):
    """Управление избранными услугами"""
    permission_classes = [IsAuthenticated]

    def list(self, request):
        """GET /api/market/favorites/ - получить избранное пользователя"""
        favorites = Favorite.objects.filter(
            user_id=request.user.id
        ).select_related('service').order_by('-created_at')
        
        serializer = FavoriteSerializer(favorites, many=True, context={'request': request})
        
        return Response({
            'status': 'success',
            'data': serializer.data,
            'error': None
        })

    def create(self, request):
        """POST /api/market/favorites/ - добавить в избранное"""
        service_id = request.data.get('service_id')
        
        if not service_id:
            return Response({
                'status': 'error',
                'error': 'service_id обязателен',
                'data': None
            }, status=400)
        
        try:
            service = Service.objects.get(id=service_id)
        except Service.DoesNotExist:
            return Response({
                'status': 'error',
                'error': 'Услуга не найдена',
                'data': None
            }, status=404)
        
        # Проверяем, не добавлено ли уже
        favorite, created = Favorite.objects.get_or_create(
            user_id=request.user.id,
            service=service
        )
        
        if not created:
            return Response({
                'status': 'success',
                'data': FavoriteSerializer(favorite, context={'request': request}).data,
                'message': 'Уже в избранном'
            })
        
        return Response({
            'status': 'success',
            'data': FavoriteSerializer(favorite, context={'request': request}).data,
            'message': 'Добавлено в избранное'
        }, status=201)

    def destroy(self, request, pk=None):
        """DELETE /api/market/favorites/{id}/ - удалить из избранного"""
        try:
            favorite = Favorite.objects.get(
                id=pk,
                user_id=request.user.id
            )
            
            favorite.delete()
            
            return Response({
                'status': 'success',
                'message': 'Удалено из избранного'
            })
            
        except Favorite.DoesNotExist:
            return Response({
                'status': 'error',
                'error': 'Не найдено в избранном',
                'data': None
            }, status=404)

    @action(detail=False, methods=['post'], url_path='toggle')
    def toggle(self, request):
        """POST /api/market/favorites/toggle/ - переключить избранное (add/remove)"""
        service_id = request.data.get('service_id')
        
        if not service_id:
            return Response({
                'status': 'error',
                'error': 'service_id обязателен',
                'data': None
            }, status=400)
        
        try:
            service = Service.objects.get(id=service_id)
        except Service.DoesNotExist:
            return Response({
                'status': 'error',
                'error': 'Услуга не найдена',
                'data': None
            }, status=404)
        
        favorite = Favorite.objects.filter(
            user_id=request.user.id,
            service=service
        ).first()
        
        if favorite:
            # Удаляем
            favorite.delete()
            return Response({
                'status': 'success',
                'data': {
                    'is_favorited': False,
                    'service_id': str(service_id)
                },
                'message': 'Удалено из избранного'
            })
        else:
            # Добавляем
            favorite = Favorite.objects.create(
                user_id=request.user.id,
                service=service
            )
            return Response({
                'status': 'success',
                'data': {
                    'is_favorited': True,
                    'service_id': str(service_id),
                    'favorite_id': str(favorite.id)
                },
                'message': 'Добавлено в избранное'
            }, status=201)


class DealViewSet(viewsets.ViewSet):
    """API для работы с заказами"""
    permission_classes = [IsAuthenticated]

    def list(self, request):
        """Получить все заказы пользователя"""
        user_id = request.user.id
        deals = Deal.objects.filter(
            Q(client_id=user_id) | Q(worker_id=user_id)
        ).order_by('-created_at')

        serializer = DealSerializer(deals, many=True)
        return Response({'status': 'success', 'data': serializer.data})

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
        """Получить все заказы для чата"""
        user_id = str(request.user.id)
        
        deals = Deal.objects.filter(
            chat_room_id=chat_room_id
        ).filter(
            Q(client_id=user_id) | Q(worker_id=user_id)
        ).order_by('-created_at')

        serializer = DealSerializer(deals, many=True)
        return Response({'status': 'success', 'data': serializer.data})

    @action(detail=False, methods=['post'], url_path='create', throttle_classes=[DealCreationThrottle])
    def create_deal(self, request):
        """Создать новый заказ"""
        serializer = CreateDealSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({'error': serializer.errors}, status=400)

        try:
            auth_header = request.headers.get('Authorization', '')
            token = auth_header.split(' ')[1] if auth_header.startswith('Bearer ') else ''

            import requests as req
            chat_url = f"http://localhost:8003/api/chat/rooms/{serializer.validated_data['chat_room_id']}/"
            chat_response = req.get(chat_url, headers={'Authorization': f'Bearer {token}'})

            if chat_response.status_code != 200:
                return Response({'error': 'Не удалось получить данные чата'}, status=400)

            chat_data = chat_response.json()
            members = chat_data['data']['members']

            current_user_id = str(request.user.id)
            
            other_member_id = None
            for member_id in members:
                if str(member_id) != current_user_id:
                    other_member_id = str(member_id)
                    break
            
            if not other_member_id:
                return Response({'error': 'Не найден второй участник чата'}, status=400)

            client_id = current_user_id
            worker_id = other_member_id

            deal = DealService.create_deal(
                chat_room_id=serializer.validated_data['chat_room_id'],
                client_id=client_id,
                worker_id=worker_id,
                title=serializer.validated_data['title'],
                description=serializer.validated_data['description'],
                price=serializer.validated_data['price'],
                auth_token=token
            )

            return Response({
                'status': 'success',
                'data': DealSerializer(deal).data,
                'message': 'Заказ создан. Ожидает оплаты.'
            })

        except ValueError as e:
            return Response({'error': str(e)}, status=400)
        except Exception as e:
            return Response({'error': str(e)}, status=400)

    @action(detail=True, methods=['patch'], url_path='update-price')
    def update_price(self, request, pk=None):
        """Изменить цену заказа"""
        try:
            deal = Deal.objects.get(id=pk)
            new_price = request.data.get('price')

            if not new_price:
                return Response({'error': 'Укажите новую цену'}, status=400)

            auth_header = request.headers.get('Authorization', '')
            token = auth_header.split(' ')[1] if auth_header.startswith('Bearer ') else ''

            deal = DealService.update_price(deal, str(request.user.id), new_price, token)

            return Response({
                'status': 'success',
                'data': DealSerializer(deal).data,
                'message': f'Цена изменена на {new_price}₽'
            })

        except Deal.DoesNotExist:
            return Response({'error': 'Заказ не найден'}, status=404)
        except Exception as e:
            return Response({'error': str(e)}, status=400)

    @action(detail=True, methods=['post'], url_path='pay', throttle_classes=[DealPaymentThrottle])
    def pay(self, request, pk=None):
        """Оплатить заказ"""
        try:
            deal = Deal.objects.get(id=pk)
            
            auth_header = request.headers.get('Authorization', '')
            token = auth_header.split(' ')[1] if auth_header.startswith('Bearer ') else ''

            deal = DealService.pay_deal(deal, str(request.user.id), token)

            return Response({
                'status': 'success',
                'data': DealSerializer(deal).data,
                'message': 'Заказ оплачен!'
            })

        except Deal.DoesNotExist:
            return Response({'error': 'Заказ не найден'}, status=404)
        except Exception as e:
            return Response({'error': str(e)}, status=400)

    @action(detail=True, methods=['post'], url_path='deliver', throttle_classes=[FileUploadThrottle])
    def deliver(self, request, pk=None):
        """Сдать работу с файлами"""
        try:
            deal = Deal.objects.get(id=pk)
            delivery_message = request.data.get('delivery_message', '')
        
            files = request.FILES.getlist('files')
            for file in files:
                if file.size > 20 * 1024 * 1024:
                    return Response({'error': f'Файл {file.name} слишком большой (макс 20MB)'}, status=400)
            
                DealDeliveryAttachment.objects.create(
                    deal=deal,
                    file=file,
                    filename=file.name,
                    file_size=file.size,
                    content_type=file.content_type or 'application/octet-stream'
                )

            auth_header = request.headers.get('Authorization', '')
            token = auth_header.split(' ')[1] if auth_header.startswith('Bearer ') else ''

            deal = DealService.deliver_work(deal, str(request.user.id), delivery_message, token)

            return Response({
                'status': 'success',
                'data': DealSerializer(deal, context={'request': request}).data,
                'message': 'Работа сдана!'
            })

        except Deal.DoesNotExist:
            return Response({'error': 'Заказ не найден'}, status=404)
        except Exception as e:
            return Response({'error': str(e)}, status=400)

    @action(detail=True, methods=['post'], url_path='revision')
    def revision(self, request, pk=None):
        """Запросить доработку"""
        try:
            deal = Deal.objects.get(id=pk)
            revision_reason = request.data.get('revision_reason', '')

            auth_header = request.headers.get('Authorization', '')
            token = auth_header.split(' ')[1] if auth_header.startswith('Bearer ') else ''

            deal = DealService.request_revision(deal, str(request.user.id), revision_reason, token)

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
        """Завершить заказ с отзывом"""
        try:
            deal = Deal.objects.get(id=pk)
            
            serializer = CompleteDealSerializer(data=request.data)
            if not serializer.is_valid():
                return Response({'error': serializer.errors}, status=400)

            auth_header = request.headers.get('Authorization', '')
            token = auth_header.split(' ')[1] if auth_header.startswith('Bearer ') else ''

            deal = DealService.complete_deal(
                deal=deal,
                client_id=str(request.user.id),
                rating=serializer.validated_data['rating'],
                comment=serializer.validated_data.get('comment', ''),
                auth_token=token
            )

            return Response({
                'status': 'success',
                'data': DealSerializer(deal).data,
                'message': 'Заказ завершён!'
            })

        except Deal.DoesNotExist:
            return Response({'error': 'Заказ не найден'}, status=404)
        except Exception as e:
            return Response({'error': str(e)}, status=400)

    @action(detail=True, methods=['post'], url_path='cancel')
    def cancel(self, request, pk=None):
        """Отменить заказ"""
        try:
            deal = Deal.objects.get(id=pk)
            reason = request.data.get('reason', 'Не указана')
            
            auth_header = request.headers.get('Authorization', '')
            token = auth_header.split(' ')[1] if auth_header.startswith('Bearer ') else ''

            deal = DealService.cancel_deal(deal, str(request.user.id), reason, token)

            return Response({
                'status': 'success',
                'data': DealSerializer(deal).data,
                'message': 'Заказ отменён'
            })

        except Deal.DoesNotExist:
            return Response({'error': 'Заказ не найден'}, status=404)
        except Exception as e:
            return Response({'error': str(e)}, status=400)

    @action(detail=False, methods=['post'], url_path='generate-tz', throttle_classes=[AIGenerationThrottle])
    def generate_tz(self, request):
        """AI-генерация ТЗ"""
        service_id = request.data.get('service_id')
        raw_requirements = request.data.get('raw_requirements')

        if not service_id or not raw_requirements:
            return Response({'error': 'service_id и raw_requirements обязательны'}, status=400)

        try:
            try:
                service = Service.objects.get(id=service_id)
                if not service.is_active:
                    return Response({
                        'status': 'error',
                        'error': 'Нельзя создать заказ на неактивное объявление',
                        'data': None
                    }, status=400)
            except Service.DoesNotExist:
                return Response({'error': 'Услуга не найдена'}, status=404)

            generated_tz = AIService.generate_tz(service_id, raw_requirements)

            return Response({
                'status': 'success',
                'data': {'generated_tz': generated_tz}
            })

        except Exception as e:
            return Response({'error': str(e)}, status=400)

    @action(detail=True, methods=['post'], url_path='open-dispute')
    def open_dispute(self, request, pk=None):
        """Открыть спор"""
        try:
            deal = Deal.objects.get(id=pk)
            dispute_reason = request.data.get('dispute_reason', '')

            if not dispute_reason:
                return Response({'error': 'Укажите причину спора'}, status=400)

            auth_header = request.headers.get('Authorization', '')
            token = auth_header.split(' ')[1] if auth_header.startswith('Bearer ') else ''

            deal = DealService.open_dispute(deal, str(request.user.id), dispute_reason, token)

            return Response({
                'status': 'success',
                'data': DealSerializer(deal).data,
                'message': 'Спор открыт'
            })

        except Deal.DoesNotExist:
            return Response({'error': 'Заказ не найден'}, status=404)
        except Exception as e:
            return Response({'error': str(e)}, status=400)

    @action(detail=True, methods=['post'], url_path='worker-refund')
    def worker_refund(self, request, pk=None):
        """Исполнитель возвращает деньги"""
        try:
            deal = Deal.objects.get(id=pk)

            auth_header = request.headers.get('Authorization', '')
            token = auth_header.split(' ')[1] if auth_header.startswith('Bearer ') else ''

            deal = DealService.worker_refund(deal, str(request.user.id), token)

            return Response({
                'status': 'success',
                'data': DealSerializer(deal).data,
                'message': 'Деньги возвращены клиенту'
            })

        except Deal.DoesNotExist:
            return Response({'error': 'Заказ не найден'}, status=404)
        except Exception as e:
            return Response({'error': str(e)}, status=400)

    @action(detail=True, methods=['post'], url_path='worker-defend')
    def worker_defend(self, request, pk=None):
        """Исполнитель оспаривает претензию"""
        try:
            deal = Deal.objects.get(id=pk)
            defense_text = request.data.get('defense_text', '')

            if not defense_text:
                return Response({'error': 'Укажите аргументы защиты'}, status=400)

            auth_header = request.headers.get('Authorization', '')
            token = auth_header.split(' ')[1] if auth_header.startswith('Bearer ') else ''

            deal = DealService.worker_defend(deal, str(request.user.id), defense_text, token)

            return Response({
                'status': 'success',
                'data': DealSerializer(deal).data,
                'message': 'Защита подана. Спор передан администратору.'
            })

        except Deal.DoesNotExist:
            return Response({'error': 'Заказ не найден'}, status=404)
        except Exception as e:
            return Response({'error': str(e)}, status=400)

    @action(detail=True, methods=['post'], url_path='admin-resolve')
    def admin_resolve(self, request, pk=None):
        """Администратор разрешает спор"""
        try:
            deal = Deal.objects.get(id=pk)
            winner = request.data.get('winner')
            admin_comment = request.data.get('admin_comment', '')

            if not winner:
                return Response({'error': 'Укажите победителя (client/worker)'}, status=400)

            auth_header = request.headers.get('Authorization', '')
            token = auth_header.split(' ')[1] if auth_header.startswith('Bearer ') else ''

            deal = DealService.admin_resolve_dispute(deal, winner, admin_comment, token)

            return Response({
                'status': 'success',
                'data': DealSerializer(deal).data,
                'message': f'Спор разрешен в пользу {"клиента" if winner == "client" else "исполнителя"}'
            })

        except Deal.DoesNotExist:
            return Response({'error': 'Заказ не найден'}, status=404)
        except Exception as e:
            return Response({'error': str(e)}, status=400)

    @action(detail=False, methods=['get'], url_path='pending-disputes')
    def pending_disputes(self, request):
        """Получить все активные споры"""
        disputes = Deal.objects.filter(
            status='dispute',
            dispute_worker_defense__isnull=False,
            dispute_winner=''
        ).order_by('-dispute_created_at')

        serializer = DealSerializer(disputes, many=True)
        return Response({
            'status': 'success',
            'data': serializer.data
        })


class ReviewViewSet(viewsets.ReadOnlyModelViewSet):
    """Просмотр отзывов"""
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [AllowAny]

    @action(detail=False, methods=['get'], url_path='by-worker/(?P<worker_id>[^/.]+)')
    def by_worker(self, request, worker_id=None):
        """Получить все отзывы исполнителя"""
        reviews = Review.objects.filter(reviewee_id=worker_id).order_by('-created_at')
        serializer = self.get_serializer(reviews, many=True)
        return Response({'status': 'success', 'data': serializer.data})


class UpdateOwnerAvatarView(APIView):
    """Обновление аватара владельца во всех его объявлениях"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Обновить owner_avatar во всех объявлениях пользователя"""
        owner_id = request.data.get('owner_id')
        owner_avatar = request.data.get('owner_avatar', '')
        
        if not owner_id:
            return Response({'error': 'owner_id обязателен'}, status=400)
        
        if str(request.user.id) != str(owner_id):
            return Response({'error': 'Нет прав'}, status=403)
        
        count = Service.objects.filter(owner_id=owner_id).update(owner_avatar=owner_avatar)
        
        return Response({
            'status': 'success',
            'data': {'updated_count': count},
            'message': f'Обновлено объявлений: {count}'
        })
