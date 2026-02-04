from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from .serializers import (
    RegisterSerializer, 
    LoginSerializer, 
    UserSerializer, 
    ProfileSerializer,
    SubscriptionSerializer
)
from .services import AuthService
from .models import (
    User, Subscription, SubscriptionPayment, Service, TelegramLinkToken, 
    Profile, LoginAttempt, EmailVerification, PasswordResetToken
)
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
        if settings.DEBUG:
            return True
        return False
    
    TEST_SECRET_KEY = '6LeIxAcTAAAAAGG-vFI1TnRWxMZNFuojJ4WifJWe'
    if secret_key == TEST_SECRET_KEY and settings.DEBUG:
        print("⚠️ Используются тестовые ключи reCAPTCHA (только для разработки!)")
        return True
    
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
        
        if settings.DEBUG:
            print(f"reCAPTCHA response: {result}")
        
        return result.get('success', False)
    except Exception as e:
        print(f"reCAPTCHA verification error: {e}")
        if settings.DEBUG:
            return True
        return False


def send_verification_email(user, code, verification_type='registration', new_email=None):
    """Отправка email с кодом подтверждения"""
    import ssl
    
    try:
        email_to_send = new_email if new_email else user.email
        
        if verification_type == 'email_change':
            subject = 'Подтверждение смены email - Mvs-Work'
            message = f'''
Здравствуйте!

Вы запросили смену email на вашем аккаунте Mvs-Work.

Ваш код подтверждения: {code}

Код действителен в течение 15 минут.

Если вы не запрашивали смену email, проигнорируйте это письмо.

С уважением,
Команда Mvs-Work
            '''
        else:
            subject = 'Подтверждение email - Mvs-Work'
            message = f'''
Здравствуйте!

Ваш код подтверждения: {code}

Код действителен в течение 15 минут.

Если вы не регистрировались на Mvs-Work, проигнорируйте это письмо.

С уважением,
Команда Mvs-Work
            '''
        
        import smtplib
        from email.mime.text import MIMEText
        
        msg = MIMEText(message)
        msg['Subject'] = subject
        msg['From'] = settings.DEFAULT_FROM_EMAIL
        msg['To'] = email_to_send
        
        context = ssl._create_unverified_context()
        
        with smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT, timeout=10) as server:
            server.starttls(context=context)
            server.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
            server.send_message(msg)
        
        return True
        
    except Exception as e:
        print(f"❌ Email sending error: {e}")
        return False


def send_password_reset_email(user, token):
    """Отправка email с ссылкой для сброса пароля"""
    import ssl
    
    try:
        frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:5173')
        reset_link = f"{frontend_url}/reset-password?token={token}"
        
        subject = 'Сброс пароля - Mvs-Work'
        message = f'''
Здравствуйте!

Вы запросили сброс пароля на вашем аккаунте Mvs-Work.

Перейдите по ссылке для сброса пароля:
{reset_link}

Ссылка действительна в течение 1 часа.

Если вы не запрашивали сброс пароля, проигнорируйте это письмо.

С уважением,
Команда Mvs-Work
        '''
        
        import smtplib
        from email.mime.text import MIMEText
        
        msg = MIMEText(message)
        msg['Subject'] = subject
        msg['From'] = settings.DEFAULT_FROM_EMAIL
        msg['To'] = user.email
        
        context = ssl._create_unverified_context()
        
        with smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT, timeout=10) as server:
            server.starttls(context=context)
            server.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
            server.send_message(msg)
        
        return True
        
    except Exception as e:
        print(f"❌ Password reset email error: {e}")
        return False


class CookieTokenRefreshView(TokenRefreshView):
    """Кастомный refresh view который читает refresh token из cookie"""
    permission_classes = [AllowAny]
    
    def post(self, request, *args, **kwargs):
        refresh_token = request.COOKIES.get('refresh_token')
        
        if not refresh_token:
            return Response({
                'error': 'Refresh token not found'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        try:
            refresh = RefreshToken(refresh_token)
            access_token = str(refresh.access_token)
            
            return Response({
                'access': access_token
            }, status=status.HTTP_200_OK)
            
        except TokenError:
            return Response({
                'error': 'Invalid or expired refresh token'
            }, status=status.HTTP_401_UNAUTHORIZED)


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
            
            verification = EmailVerification.create_for_user(
                user, 
                verification_type='registration'
            )
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
        
        if not verify_recaptcha(recaptcha_token):
            return Response({
                'status': 'error',
                'error': 'reCAPTCHA проверка не пройдена',
                'data': None
            }, status=status.HTTP_400_BAD_REQUEST)
        
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
            log_login_attempt(email, ip_address, successful=False)
            
            return Response({
                'status': 'error',
                'error': str(e),
                'data': None
            }, status=status.HTTP_401_UNAUTHORIZED)


class LogoutView(APIView):
    """Выход из системы - удаление refresh token из cookies"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        response = Response({
            'status': 'success',
            'message': 'Logged out successfully'
        }, status=status.HTTP_200_OK)
        
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
            
            # Если это смена email
            if verification.verification_type == 'email_change' and verification.new_email:
                # Проверяем, что новый email не занят
                if User.objects.filter(email=verification.new_email).exclude(id=request.user.id).exists():
                    return Response({
                        'status': 'error',
                        'error': 'Этот email уже используется'
                    }, status=400)
                
                # Меняем email
                request.user.email = verification.new_email
                request.user.email_verified = True
                request.user.save()
            else:
                # Обычное подтверждение
                request.user.email_verified = True
                request.user.save()
            
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
        
        verification = EmailVerification.create_for_user(
            request.user,
            verification_type='registration'
        )
        
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


class UpdateEmailView(APIView):
    """Обновление email на странице верификации"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        new_email = request.data.get('new_email')
        
        if not new_email:
            return Response({
                'status': 'error',
                'error': 'Новый email обязателен'
            }, status=400)
        
        # Проверка формата email
        from django.core.validators import validate_email as django_validate_email
        from django.core.exceptions import ValidationError
        
        try:
            django_validate_email(new_email)
        except ValidationError:
            return Response({
                'status': 'error',
                'error': 'Неверный формат email'
            }, status=400)
        
        # Проверка, что email не занят
        if User.objects.filter(email=new_email).exclude(id=request.user.id).exists():
            return Response({
                'status': 'error',
                'error': 'Этот email уже используется'
            }, status=400)
        
        # Меняем email и сбрасываем верификацию
        request.user.email = new_email
        request.user.email_verified = False
        request.user.save()
        
        # Создаем новый код верификации
        verification = EmailVerification.create_for_user(
            request.user,
            verification_type='registration'
        )
        
        if send_verification_email(request.user, verification.code):
            return Response({
                'status': 'success',
                'data': UserSerializer(request.user, context={'request': request}).data,
                'message': 'Email обновлен. Код отправлен на новый адрес.'
            })
        else:
            return Response({
                'status': 'error',
                'error': 'Email обновлен, но не удалось отправить код'
            }, status=500)


class RequestEmailChangeView(APIView):
    """Запрос на смену email из профиля"""
    permission_classes = [IsAuthenticated]
    throttle_classes = [ProfileUpdateThrottle]
    
    def post(self, request):
        new_email = request.data.get('new_email')
        
        if not new_email:
            return Response({
                'status': 'error',
                'error': 'Новый email обязателен'
            }, status=400)
        
        # Проверка формата email
        from django.core.validators import validate_email as django_validate_email
        from django.core.exceptions import ValidationError
        
        try:
            django_validate_email(new_email)
        except ValidationError:
            return Response({
                'status': 'error',
                'error': 'Неверный формат email'
            }, status=400)
        
        # Проверка, что email не занят
        if User.objects.filter(email=new_email).exists():
            return Response({
                'status': 'error',
                'error': 'Этот email уже используется'
            }, status=400)
        
        # Создаем код верификации для смены email
        verification = EmailVerification.create_for_user(
            request.user,
            verification_type='email_change',
            new_email=new_email
        )
        
        if send_verification_email(
            request.user, 
            verification.code, 
            verification_type='email_change',
            new_email=new_email
        ):
            return Response({
                'status': 'success',
                'message': f'Код подтверждения отправлен на {new_email}'
            })
        else:
            return Response({
                'status': 'error',
                'error': 'Не удалось отправить email'
            }, status=500)


class ConfirmEmailChangeView(APIView):
    """Подтверждение смены email"""
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
                verification_type='email_change',
                used=False
            )
            
            if not verification.is_valid():
                return Response({
                    'status': 'error',
                    'error': 'Код истек или уже использован'
                }, status=400)
            
            if not verification.new_email:
                return Response({
                    'status': 'error',
                    'error': 'Новый email не найден'
                }, status=400)
            
            # Проверяем, что новый email не занят
            if User.objects.filter(email=verification.new_email).exclude(id=request.user.id).exists():
                return Response({
                    'status': 'error',
                    'error': 'Этот email уже используется'
                }, status=400)
            
            # Меняем email
            request.user.email = verification.new_email
            request.user.save()
            
            verification.used = True
            verification.save()
            
            return Response({
                'status': 'success',
                'data': UserSerializer(request.user, context={'request': request}).data,
                'message': 'Email успешно изменен'
            })
            
        except EmailVerification.DoesNotExist:
            return Response({
                'status': 'error',
                'error': 'Неверный код'
            }, status=400)


class ForgotPasswordView(APIView):
    """Запрос на сброс пароля"""
    permission_classes = [AllowAny]
    throttle_classes = [AuthenticationThrottle]
    
    def post(self, request):
        email = request.data.get('email')
        
        if not email:
            return Response({
                'status': 'error',
                'error': 'Email обязателен'
            }, status=400)
        
        try:
            user = User.objects.get(email=email)
            
            # Создаем токен для сброса пароля
            reset_token = PasswordResetToken.create_for_user(user)
            
            # Отправляем email
            if send_password_reset_email(user, reset_token.token):
                return Response({
                    'status': 'success',
                    'message': 'Ссылка для сброса пароля отправлена на email'
                })
            else:
                return Response({
                    'status': 'error',
                    'error': 'Не удалось отправить email'
                }, status=500)
                
        except User.DoesNotExist:
            # Не раскрываем, существует ли пользователь
            return Response({
                'status': 'success',
                'message': 'Если такой email существует, ссылка для сброса пароля отправлена'
            })


class ResetPasswordView(APIView):
    """Сброс пароля по токену"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        token = request.data.get('token')
        new_password = request.data.get('new_password')
        
        if not token or not new_password:
            return Response({
                'status': 'error',
                'error': 'Токен и новый пароль обязательны'
            }, status=400)
        
        if len(new_password) < 6:
            return Response({
                'status': 'error',
                'error': 'Пароль должен быть не менее 6 символов'
            }, status=400)
        
        try:
            reset_token = PasswordResetToken.objects.get(token=token, used=False)
            
            if not reset_token.is_valid():
                return Response({
                    'status': 'error',
                    'error': 'Токен истек или уже использован'
                }, status=400)
            
            # Меняем пароль
            user = reset_token.user
            user.set_password(new_password)
            user.save()
            
            # Отмечаем токен как использованный
            reset_token.used = True
            reset_token.save()
            
            return Response({
                'status': 'success',
                'message': 'Пароль успешно изменен'
            })
            
        except PasswordResetToken.DoesNotExist:
            return Response({
                'status': 'error',
                'error': 'Неверный или истекший токен'
            }, status=400)


class ChangePasswordView(APIView):
    """Смена пароля для авторизованного пользователя"""
    permission_classes = [IsAuthenticated]
    throttle_classes = [ProfileUpdateThrottle]
    
    def post(self, request):
        old_password = request.data.get('old_password')
        new_password = request.data.get('new_password')
        
        if not old_password or not new_password:
            return Response({
                'status': 'error',
                'error': 'Старый и новый пароль обязательны'
            }, status=400)
        
        # Проверяем старый пароль
        if not request.user.check_password(old_password):
            return Response({
                'status': 'error',
                'error': 'Неверный текущий пароль'
            }, status=400)
        
        # Валидация нового пароля
        if len(new_password) < 6:
            return Response({
                'status': 'error',
                'error': 'Новый пароль должен быть не менее 6 символов'
            }, status=400)
        
        # Меняем пароль
        request.user.set_password(new_password)
        request.user.save()
        
        return Response({
            'status': 'success',
            'message': 'Пароль успешно изменен'
        })


class DeleteAccountView(APIView):
    """Полное удаление аккаунта"""
    permission_classes = [IsAuthenticated]
    
    @transaction.atomic
    def delete(self, request):
        password = request.data.get('password')
        
        if not password:
            return Response({
                'status': 'error',
                'error': 'Пароль обязателен для удаления аккаунта'
            }, status=400)
        
        # Проверяем пароль
        if not request.user.check_password(password):
            return Response({
                'status': 'error',
                'error': 'Неверный пароль'
            }, status=400)
        
        user = request.user
        
        # Удаляем пользователя (каскадно удалятся связанные объекты)
        user.delete()
        
        response = Response({
            'status': 'success',
            'message': 'Аккаунт успешно удален'
        })
        
        # Удаляем refresh token
        response.delete_cookie(
            'refresh_token',
            path='/',
            samesite='Lax'
        )
        
        return response


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
