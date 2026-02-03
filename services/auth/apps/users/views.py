from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .serializers import (
    RegisterSerializer, 
    LoginSerializer, 
    UserSerializer, 
    ProfileSerializer,
    SubscriptionSerializer
)
from .services import AuthService
from .models import User, Subscription, SubscriptionPayment, Service, TelegramLinkToken, Profile, LoginAttempt, EmailVerification
from .throttling import (
    AuthenticationThrottle, 
    SubscriptionThrottle, 
    ProfileUpdateThrottle,
    TelegramLinkThrottle
)
from django.db import transaction
from django.utils import timezone
from django.conf import settings
from datetime import timedelta
import requests
import os
import secrets
from django.core.mail import send_mail


def get_client_ip(request):
    """Получить IP адрес клиента"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def check_login_attempts(email, ip_address):
    """Проверить количество попыток входа"""
    timeout = settings.LOGIN_ATTEMPT_TIMEOUT
    limit = settings.LOGIN_ATTEMPT_LIMIT
    
    cutoff_time = timezone.now() - timedelta(seconds=timeout)
    
    recent_attempts = LoginAttempt.objects.filter(
        email=email,
        attempt_time__gte=cutoff_time,
        successful=False
    ).count()
    
    return recent_attempts < limit


def log_login_attempt(email, ip_address, successful):
    """Записать попытку входа"""
    LoginAttempt.objects.create(
        email=email,
        ip_address=ip_address,
        successful=successful
    )


def verify_recaptcha(token):
    """Проверка reCAPTCHA токена"""
    secret_key = os.getenv('RECAPTCHA_SECRET_KEY')
    
    if not secret_key:
        # В dev режиме без ключа пропускаем
        if settings.DEBUG:
            return True
        return False
    
    try:
        response = requests.post(
            'https://www.google.com/recaptcha/api/siteverify',
            data={
                'secret': secret_key,
                'response': token
            },
            timeout=5
        )
        
        result = response.json()
        return result.get('success', False)
    except Exception as e:
        print(f"reCAPTCHA verification error: {e}")
        return False


def send_verification_email(user, code):
    """Отправка email с кодом подтверждения"""
    try:
        subject = 'Подтверждение email - Mvs-Work'
        message = f'''
Здравствуйте!

Ваш код подтверждения: {code}

Код действителен в течение 15 минут.

Если вы не регистрировались на Mvs-Work, проигнорируйте это письмо.

С уважением,
Команда Mvs-Work
        '''
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Email sending error: {e}")
        return False


class CookieTokenObtainPairView(TokenObtainPairView):
    """Кастомный login view с сохранением refresh token в httpOnly cookie"""
    
    def finalize_response(self, request, response, *args, **kwargs):
        if response.data.get('refresh'):
            response.set_cookie(
                key='refresh_token',
                value=response.data['refresh'],
                httponly=True,
                secure=not settings.DEBUG,
                samesite='Lax',
                max_age=7*24*60*60,
                path='/'
            )
            del response.data['refresh']
        
        return super().finalize_response(request, response, *args, **kwargs)


class CookieTokenRefreshView(TokenRefreshView):
    """Кастомный refresh view который читает refresh token из cookie"""
    
    def post(self, request, *args, **kwargs):
        refresh_token = request.COOKIES.get('refresh_token')
        
        if not refresh_token:
            refresh_token = request.data.get('refresh')
        
        if not refresh_token:
            return Response({
                'status': 'error',
                'error': 'Refresh token not found',
                'data': None
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        request._full_data = {'refresh': refresh_token}
        
        return super().post(request, *args, **kwargs)


class RegisterView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [AuthenticationThrottle]

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
            
            # Создаем код верификации
            verification = EmailVerification.create_for_user(user)
            
            # Отправляем email
            send_verification_email(user, verification.code)
            
            response_data = {
                'status': 'success',
                'data': {
                    'user': UserSerializer(user, context={'request': request}).data,
                    'tokens': {
                        'access': tokens['access']
                    }
                },
                'error': None
            }
            
            response = Response(response_data, status=status.HTTP_201_CREATED)
            
            response.set_cookie(
                key='refresh_token',
                value=tokens['refresh'],
                httponly=True,
                secure=not settings.DEBUG,
                samesite='Lax',
                max_age=7*24*60*60,
                path='/'
            )
            
            return response
            
        except Exception as e:
            return Response({
                'status': 'error',
                'error': str(e),
                'data': None
            }, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [AuthenticationThrottle]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response({
                'status': 'error',
                'error': serializer.errors,
                'data': None
            }, status=status.HTTP_400_BAD_REQUEST)
        
        email = serializer.validated_data['email']
        recaptcha_token = serializer.validated_data['recaptcha_token']
        ip_address = get_client_ip(request)
        
        # Проверка reCAPTCHA
        if not verify_recaptcha(recaptcha_token):
            return Response({
                'status': 'error',
                'error': 'reCAPTCHA проверка не пройдена',
                'data': None
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Проверка количества попыток
        if not check_login_attempts(email, ip_address):
            return Response({
                'status': 'error',
                'error': 'Слишком много попыток входа. Попробуйте через 5 минут.',
                'data': None
            }, status=status.HTTP_429_TOO_MANY_REQUESTS)
        
        try:
            user, tokens = AuthService.login_user(
                email=email,
                password=serializer.validated_data['password']
            )
            
            # Успешный вход
            log_login_attempt(email, ip_address, successful=True)
            
            response_data = {
                'status': 'success',
                'data': {
                    'user': UserSerializer(user, context={'request': request}).data,
                    'tokens': {
                        'access': tokens['access']
                    }
                },
                'error': None
            }
            
            response = Response(response_data, status=status.HTTP_200_OK)
            
            response.set_cookie(
                key='refresh_token',
                value=tokens['refresh'],
                httponly=True,
                secure=not settings.DEBUG,
                samesite='Lax',
                max_age=7*24*60*60,
                path='/'
            )
            
            return response
            
        except ValueError as e:
            # Неудачная попытка
            log_login_attempt(email, ip_address, successful=False)
            
            return Response({
                'status': 'error',
                'error': str(e),
                'data': None
            }, status=status.HTTP_401_UNAUTHORIZED)


class LogoutView(APIView):
    """Выход из системы - удаление refresh token из cookies"""
    permission_classes = [AllowAny]  # Разрешаем всем, даже если токен невалидный
    
    def post(self, request):
        response = Response({
            'status': 'success',
            'message': 'Logged out successfully'
        }, status=status.HTTP_200_OK)
        
        # Удаляем refresh_token из cookies
        response.delete_cookie(
            'refresh_token',
            path='/',
            samesite='Lax'
        )
        
        return response


class VerifyEmailView(APIView):
    """Подтверждение email по коду"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        code = request.data.get('code')
        
        if not code:
            return Response({
                'status': 'error',
                'error': 'Код обязателен'
            }, status=400)
        
        try:
            verification = EmailVerification.objects.get(
                user=request.user,
                code=code,
                used=False
            )
            
            if not verification.is_valid():
                return Response({
                    'status': 'error',
                    'error': 'Код истек или уже использован'
                }, status=400)
            
            # Подтверждаем email
            request.user.email_verified = True
            request.user.save()
            
            # Помечаем код как использованный
            verification.used = True
            verification.save()
            
            return Response({
                'status': 'success',
                'data': UserSerializer(request.user, context={'request': request}).data,
                'message': 'Email успешно подтвержден'
            })
            
        except EmailVerification.DoesNotExist:
            return Response({
                'status': 'error',
                'error': 'Неверный код'
            }, status=400)


class ResendVerificationView(APIView):
    """Повторная отправка кода подтверждения"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        if request.user.email_verified:
            return Response({
                'status': 'error',
                'error': 'Email уже подтвержден'
            }, status=400)
        
        # Создаем новый код
        verification = EmailVerification.create_for_user(request.user)
        
        # Отправляем email
        if send_verification_email(request.user, verification.code):
            return Response({
                'status': 'success',
                'message': 'Код отправлен повторно'
            })
        else:
            return Response({
                'status': 'error',
                'error': 'Не удалось отправить email'
            }, status=500)


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
        throttle = ProfileUpdateThrottle()
        if not throttle.allow_request(request, self):
            return Response({
                'status': 'error',
                'error': 'Слишком много попыток обновления. Попробуйте позже.',
                'data': None
            }, status=status.HTTP_429_TOO_MANY_REQUESTS)
        
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
                
                if 'avatar' in request.data or serializer.validated_data.get('avatar'):
                    avatar_url = request.build_absolute_uri(profile.avatar.url) if profile.avatar else ''
                    
                    market_service_url = os.getenv('MARKET_SERVICE_URL', 'http://localhost:8002')
                    
                    try:
                        auth_header = request.headers.get('Authorization', '')
                        
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
    throttle_classes = [SubscriptionThrottle]

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
            subscription.check_and_update_status()
            
            return Response({
                'status': 'success',
                'data': SubscriptionSerializer(subscription).data,
                'error': None
            })
        except Subscription.DoesNotExist:
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

        payment = SubscriptionPayment.objects.create(
            subscription=subscription,
            amount=Subscription.SUBSCRIPTION_PRICE,
            status='pending',
            payment_provider='stub'
        )

        payment.status = 'completed'
        payment.save()

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


class TelegramGenerateLinkView(APIView):
    """Генерация одноразовой ссылки для привязки Telegram"""
    permission_classes = [IsAuthenticated]
    throttle_classes = [TelegramLinkThrottle]
    
    def post(self, request):
        try:
            TelegramLinkToken.objects.filter(
                user=request.user,
                used=False
            ).delete()
            
            token = secrets.token_urlsafe(32)
            
            link_token = TelegramLinkToken.objects.create(
                user=request.user,
                token=token,
                expires_at=timezone.now() + timedelta(minutes=10)
            )
            
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
            
            try:
                link_token = TelegramLinkToken.objects.get(token=token)
            except TelegramLinkToken.DoesNotExist:
                return Response({
                    'status': 'error',
                    'error': 'Неверный или истекший токен'
                }, status=status.HTTP_404_NOT_FOUND)
            
            if not link_token.is_valid():
                return Response({
                    'status': 'error',
                    'error': 'Токен истек или уже использован'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            profile = link_token.user.profile
            profile.telegram_chat_id = telegram_chat_id
            profile.telegram_notifications_enabled = True
            profile.save()
            
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


class InternalUserProfileView(APIView):
    """Внутренний эндпоинт для получения профиля (защищен JWT middleware)"""
    authentication_classes = []
    permission_classes = [AllowAny]
    
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
