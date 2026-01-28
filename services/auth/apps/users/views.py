from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from .serializers import (
    RegisterSerializer, 
    LoginSerializer, 
    UserSerializer, 
    ProfileSerializer,
    SubscriptionSerializer
)
from .services import AuthService
from .models import User, Subscription, SubscriptionPayment, Service, TelegramLinkToken, Profile
from django.db import transaction
from django.utils import timezone
from datetime import timedelta
import requests
import os
import secrets


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response({
                'status': 'error',
                'error': serializer.errors,
                'data': None
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user, tokens = AuthService.register_user(
                email=serializer.validated_data['email'],
                password=serializer.validated_data['password'],
                role=serializer.validated_data['role']
            )
            
            return Response({
                'status': 'success',
                'data': {
                    'user': UserSerializer(user, context={'request': request}).data,
                    'tokens': tokens
                },
                'error': None
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response({
                'status': 'error',
                'error': str(e),
                'data': None
            }, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response({
                'status': 'error',
                'error': serializer.errors,
                'data': None
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user, tokens = AuthService.login_user(
                email=serializer.validated_data['email'],
                password=serializer.validated_data['password']
            )
            
            return Response({
                'status': 'success',
                'data': {
                    'user': UserSerializer(user, context={'request': request}).data,
                    'tokens': tokens
                },
                'error': None
            }, status=status.HTTP_200_OK)
            
        except ValueError as e:
            return Response({
                'status': 'error',
                'error': str(e),
                'data': None
            }, status=status.HTTP_401_UNAUTHORIZED)


class ProfileView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get(self, request):
        return Response({
            'status': 'success',
            'data': UserSerializer(request.user, context={'request': request}).data,
            'error': None
        }, status=status.HTTP_200_OK)

    @transaction.atomic
    def patch(self, request):
        """Обновление профиля с поддержкой загрузки аватарки"""
        try:
            profile = request.user.profile
            
            serializer = ProfileSerializer(
                profile, 
                data=request.data, 
                partial=True,
                context={'request': request}
            )
            
            if serializer.is_valid():
                serializer.save()
                
                # ✅ СИНХРОНИЗАЦИЯ АВАТАРА: Обновляем owner_avatar во всех объявлениях пользователя
                if 'avatar' in request.data or serializer.validated_data.get('avatar'):
                    avatar_url = request.build_absolute_uri(profile.avatar.url) if profile.avatar else ''
                    
                    # Получаем market service URL из env
                    market_service_url = os.getenv('MARKET_SERVICE_URL', 'http://localhost:8002')
                    
                    try:
                        # Обновляем объявления через внешний API
                        auth_header = request.headers.get('Authorization', '')
                        
                        # Отправляем запрос на обновление аватара в объявлениях
                        update_url = f"{market_service_url}/api/market/services/update-owner-avatar/"
                        
                        requests.post(
                            update_url,
                            headers={
                                'Authorization': auth_header,
                                'Content-Type': 'application/json'
                            },
                            json={
                                'owner_id': str(request.user.id),
                                'owner_avatar': avatar_url
                            },
                            timeout=5
                        )
                    except Exception as e:
                        print(f"⚠️ Не удалось обновить аватар в объявлениях: {e}")
                
                return Response({
                    'status': 'success',
                    'data': UserSerializer(request.user, context={'request': request}).data,
                    'error': None
                }, status=status.HTTP_200_OK)
            
            return Response({
                'status': 'error',
                'error': serializer.errors,
                'data': None
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            return Response({
                'status': 'error',
                'error': str(e),
                'data': None
            }, status=status.HTTP_400_BAD_REQUEST)


class CheckBalanceView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        amount = request.data.get('amount', 0)
        has_balance = AuthService.check_balance(request.user.id, float(amount))

        return Response({
            'status': 'success',
            'data': {'has_balance': has_balance},
            'error': None
        }, status=status.HTTP_200_OK)


class BatchUsersView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Получить публичные данные (имя, аватар) для списка ID"""
        user_ids = request.data.get('user_ids', [])
        users = User.objects.filter(id__in=list(set(user_ids)))
        
        data = []
        for user in users:
            try:
                profile = user.profile
                display_name = profile.company_name or profile.full_name or user.email.split('@')[0]
                
                avatar_url = None
                if profile.avatar:
                    avatar_url = request.build_absolute_uri(profile.avatar.url)
                
            except:
                display_name = "Unknown User"
                avatar_url = None
            
            data.append({
                'id': str(user.id),
                'name': display_name,
                'avatar': avatar_url,
                'role': user.role
            })
            
        return Response({'status': 'success', 'data': data})


class PublicProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, user_id):
        """Получить публичный профиль пользователя"""
        try:
            user = User.objects.get(id=user_id)
            profile = user.profile
            
            data = {
                'id': str(user.id),
                'email': user.email,
                'role': user.role,
                'created_at': user.created_at,
                'profile': {
                    'full_name': profile.full_name,
                    'company_name': profile.company_name,
                    'headline': profile.headline,
                    'company_website': profile.company_website,
                    'avatar_url': request.build_absolute_uri(profile.avatar.url) if profile.avatar else None,
                    'bio': profile.bio,
                    'skills': profile.skills,
                    'rating': str(profile.rating),
                    'github_link': profile.github_link,
                    'behance_link': profile.behance_link,
                }
            }
            
            return Response({
                'status': 'success',
                'data': data,
                'error': None
            }, status=status.HTTP_200_OK)
            
        except User.DoesNotExist:
            return Response({
                'status': 'error',
                'error': 'Пользователь не найден',
                'data': None
            }, status=status.HTTP_404_NOT_FOUND)


class SubscriptionView(APIView):
    """Управление подпиской"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Получить информацию о подписке"""
        if request.user.role != 'worker':
            return Response({
                'status': 'error',
                'error': 'Подписка доступна только для воркеров',
                'data': None
            }, status=status.HTTP_403_FORBIDDEN)

        try:
            subscription = request.user.subscription
            # Проверяем и обновляем статус
            subscription.check_and_update_status()
            
            return Response({
                'status': 'success',
                'data': SubscriptionSerializer(subscription).data,
                'error': None
            })
        except Subscription.DoesNotExist:
            # Создаем подписку если её нет
            subscription = Subscription.objects.create(user=request.user, is_active=False)
            return Response({
                'status': 'success',
                'data': SubscriptionSerializer(subscription).data,
                'error': None
            })

    @transaction.atomic
    def post(self, request):
        """Оплатить подписку (заглушка)"""
        if request.user.role != 'worker':
            return Response({
                'status': 'error',
                'error': 'Подписка доступна только для воркеров',
                'data': None
            }, status=status.HTTP_403_FORBIDDEN)

        try:
            subscription = request.user.subscription
        except Subscription.DoesNotExist:
            subscription = Subscription.objects.create(user=request.user, is_active=False)

        # Создаем платеж
        payment = SubscriptionPayment.objects.create(
            subscription=subscription,
            amount=Subscription.SUBSCRIPTION_PRICE,
            status='pending',
            payment_provider='stub'
        )

        # ЗАГЛУШКА: Автоматически подтверждаем оплату
        payment.status = 'completed'
        payment.save()

        # Активируем подписку на 30 дней
        subscription.activate(duration_days=30)

        return Response({
            'status': 'success',
            'data': {
                'subscription': SubscriptionSerializer(subscription).data,
                'payment': {
                    'id': str(payment.id),
                    'amount': str(payment.amount),
                    'status': payment.status
                }
            },
            'message': 'Подписка успешно активирована на 30 дней',
            'error': None
        })


# ✅ TELEGRAM INTEGRATION VIEWS

class TelegramGenerateLinkView(APIView):
    """Генерация одноразовой ссылки для привязки Telegram"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            # Удаляем все старые неиспользованные токены
            TelegramLinkToken.objects.filter(
                user=request.user,
                used=False
            ).delete()
            
            # Генерируем новый токен
            token = secrets.token_urlsafe(32)
            
            # Создаем запись с временем жизни 10 минут
            link_token = TelegramLinkToken.objects.create(
                user=request.user,
                token=token,
                expires_at=timezone.now() + timedelta(minutes=10)
            )
            
            # Формируем ссылку на бота
            bot_username = os.getenv('TELEGRAM_BOT_USERNAME', 'your_bot')
            deep_link = f"https://t.me/{bot_username}?start={token}"
            
            return Response({
                'status': 'success',
                'data': {
                    'link': deep_link,
                    'token': token,
                    'expires_at': link_token.expires_at.isoformat()
                },
                'error': None
            })
            
        except Exception as e:
            return Response({
                'status': 'error',
                'error': str(e),
                'data': None
            }, status=status.HTTP_400_BAD_REQUEST)


class TelegramVerifyTokenView(APIView):
    """Верификация токена и привязка Telegram (вызывается ботом)"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        """Ожидает: {"token": "...", "telegram_chat_id": 123456789}"""
        try:
            token = request.data.get('token')
            telegram_chat_id = request.data.get('telegram_chat_id')
            
            if not token or not telegram_chat_id:
                return Response({
                    'status': 'error',
                    'error': 'token и telegram_chat_id обязательны'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Находим токен
            try:
                link_token = TelegramLinkToken.objects.get(token=token)
            except TelegramLinkToken.DoesNotExist:
                return Response({
                    'status': 'error',
                    'error': 'Неверный или истекший токен'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Проверяем валидность
            if not link_token.is_valid():
                return Response({
                    'status': 'error',
                    'error': 'Токен истек или уже использован'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Привязываем Telegram
            profile = link_token.user.profile
            profile.telegram_chat_id = telegram_chat_id
            profile.telegram_notifications_enabled = True
            profile.save()
            
            # Помечаем токен использованным
            link_token.used = True
            link_token.save()
            
            return Response({
                'status': 'success',
                'data': {
                    'user_email': link_token.user.email,
                    'telegram_chat_id': telegram_chat_id
                },
                'message': 'Telegram успешно привязан'
            })
            
        except Exception as e:
            return Response({
                'status': 'error',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class TelegramDisconnectView(APIView):
    """Отключение Telegram уведомлений"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            profile = request.user.profile
            profile.telegram_chat_id = None
            profile.telegram_notifications_enabled = False
            profile.save()
            
            return Response({
                'status': 'success',
                'message': 'Telegram уведомления отключены'
            })
            
        except Exception as e:
            return Response({
                'status': 'error',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class TelegramGetUserByIdView(APIView):
    """Получить user_id по telegram_chat_id (для бота)"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        """Ожидает: {"telegram_chat_id": 123456789}"""
        try:
            telegram_chat_id = request.data.get('telegram_chat_id')
            
            if not telegram_chat_id:
                return Response({
                    'status': 'error',
                    'error': 'telegram_chat_id обязателен'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            profile = Profile.objects.get(telegram_chat_id=telegram_chat_id)
            
            return Response({
                'status': 'success',
                'data': {
                    'user_id': str(profile.user.id),
                    'email': profile.user.email
                }
            })
            
        except Profile.DoesNotExist:
            return Response({
                'status': 'error',
                'error': 'Пользователь не найден'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'status': 'error',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


# ✅ INTERNAL API (защищен middleware с JWT)

class InternalUserProfileView(APIView):
    """Внутренний эндпоинт для получения профиля (защищен JWT middleware)"""
    authentication_classes = []  # ✅ Отключаем JWT аутентификацию
    permission_classes = [AllowAny]  # ✅ Защита через middleware
    
    def get(self, request, user_id):
        try:
            user = User.objects.select_related('profile').get(id=user_id)
            
            profile_data = {}
            if hasattr(user, 'profile'):
                profile_data = {
                    'full_name': user.profile.full_name,
                    'company_name': user.profile.company_name,
                    'telegram_chat_id': user.profile.telegram_chat_id,
                    'telegram_notifications_enabled': user.profile.telegram_notifications_enabled,
                }
            
            return Response({
                'status': 'success',
                'data': {
                    'id': str(user.id),
                    'email': user.email,
                    'profile': profile_data
                }
            })
        except User.DoesNotExist:
            return Response({
                'status': 'error',
                'error': 'User not found'
            }, status=404)
