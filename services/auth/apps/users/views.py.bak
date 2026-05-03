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
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def check_login_attempts(email, ip_address):
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
    LoginAttempt.objects.create(
        email=email,
        ip_address=ip_address,
        successful=successful
    )


def send_verification_email(user, code, verification_type='registration', new_email=None):
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
                'error': 'Некорректные данные',
                'data': None
            }, status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data['email']
        ip_address = get_client_ip(request)

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
                'error': 'Неверный email или пароль',
                'data': None
            }, status=status.HTTP_401_UNAUTHORIZED)
        except Exception as e:
            log_login_attempt(email, ip_address, successful=False)
            return Response({
                'status': 'error',
                'error': 'Ошибка сервера. Попробуйте позже.',
                'data': None
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class LogoutView(APIView):
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

            if verification.verification_type == 'email_change' and verification.new_email:
                if User.objects.filter(email=verification.new_email).exclude(id=request.user.id).exists():
                    return Response({
                        'status': 'error',
                        'error': 'Этот email уже используется'
                    }, status=400)

                request.user.email = verification.new_email
                request.user.email_verified = True
                request.user.save()
            else:
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
    permission_classes = [IsAuthenticated]

    def post(self, request):
        new_email = request.data.get('new_email')

        if not new_email:
            return Response({
                'status': 'error',
                'error': 'Новый email обязателен'
            }, status=400)

        from django.core.validators import validate_email as django_validate_email
        from django.core.exceptions import ValidationError

        try:
            django_validate_email(new_email)
        except ValidationError:
            return Response({
                'status': 'error',
                'error': 'Неверный формат email'
            }, status=400)

        if User.objects.filter(email=new_email).exclude(id=request.user.id).exists():
            return Response({
                'status': 'error',
                'error': 'Этот email уже используется'
            }, status=400)

        request.user.email = new_email
        request.user.email_verified = False
        request.user.save()

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
    permission_classes = [IsAuthenticated]
    throttle_classes = [ProfileUpdateThrottle]

    def post(self, request):
        new_email = request.data.get('new_email')

        if not new_email:
            return Response({
                'status': 'error',
                'error': 'Новый email обязателен'
            }, status=400)

        from django.core.validators import validate_email as django_validate_email
        from django.core.exceptions import ValidationError

        try:
            django_validate_email(new_email)
        except ValidationError:
            return Response({
                'status': 'error',
                'error': 'Неверный формат email'
            }, status=400)

        if User.objects.filter(email=new_email).exists():
            return Response({
                'status': 'error',
                'error': 'Этот email уже используется'
            }, status=400)

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

            if User.objects.filter(email=verification.new_email).exclude(id=request.user.id).exists():
                return Response({
                    'status': 'error',
                    'error': 'Этот email уже используется'
                }, status=400)

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

            reset_token = PasswordResetToken.create_for_user(user)

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
            return Response({
                'status': 'success',
                'message': 'Если такой email существует, ссылка для сброса пароля отправлена'
            })


class ResetPasswordView(APIView):
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

            user = reset_token.user
            user.set_password(new_password)
            user.save()

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

        if not request.user.check_password(old_password):
            return Response({
                'status': 'error',
                'error': 'Неверный текущий пароль'
            }, status=400)

        if len(new_password) < 6:
            return Response({
                'status': 'error',
                'error': 'Новый пароль должен быть не менее 6 символов'
            }, status=400)

        request.user.set_password(new_password)
        request.user.save()

        return Response({
            'status': 'success',
            'message': 'Пароль успешно изменен'
        })


class DeleteAccountView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def delete(self, request):
        password = request.data.get('password')

        if not password:
            return Response({
                'status': 'error',
                'error': 'Пароль обязателен для удаления аккаунта'
            }, status=400)

        if not request.user.check_password(password):
            return Response({
                'status': 'error',
                'error': 'Неверный пароль'
            }, status=400)

        user = request.user
        user.delete()

        response = Response({
            'status': 'success',
            'message': 'Аккаунт успешно удален'
        })

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

                should_update_services = (
                    'avatar' in request.data or
                    serializer.validated_data.get('avatar') or
                    'full_name' in request.data or
                    'company_name' in request.data
                )

                if should_update_services:
                    avatar_url = request.build_absolute_uri(profile.avatar.url) if profile.avatar else ''
                    owner_name = profile.company_name or profile.full_name or request.user.email.split('@')[0]
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
                                'owner_avatar': avatar_url,
                                'owner_name': owner_name
                            },
                            timeout=5
                        )
                    except Exception as e:
                        print(f"⚠️ Не удалось обновить данные в объявлениях: {e}")

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


# ─── ПОДПИСКА ЧЕРЕЗ ТОЧКА БАНК ───────────────────────────────────────────────

class SubscriptionView(APIView):
    """Управление подпиской через Точка Банк"""
    permission_classes = [IsAuthenticated]
    throttle_classes = [SubscriptionThrottle]

    def get(self, request):
        """Получить текущий статус подписки"""
        if request.user.role != 'worker':
            return Response({
                'status': 'error',
                'error': 'Подписка доступна только для исполнителей',
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
        """
        Инициировать оплату подписки через Точка Банк.

        Создаёт подписку в системе Точки и возвращает ссылку на оплату.
        Подписка активируется только после вызова /subscription/check-status/
        при получении статуса Active от Точки.

        Флоу:
          1. POST /api/auth/subscription/        → получаем payment_link
          2. Фронт открывает payment_link        → клиент оплачивает
          3. Точка редиректит на FRONTEND_URL/profile?subscription=success
          4. GET  /api/auth/subscription/check-status/ → активируем подписку
        """
        import uuid as _uuid
        import logging
        logger = logging.getLogger(__name__)

        if request.user.role != 'worker':
            return Response({
                'status': 'error',
                'error': 'Подписка доступна только для исполнителей',
                'data': None
            }, status=status.HTTP_403_FORBIDDEN)

        # Получаем или создаём запись подписки
        try:
            subscription = request.user.subscription
        except Subscription.DoesNotExist:
            subscription = Subscription.objects.create(user=request.user, is_active=False)

        # Если уже активна — не создаём новый платёж
        subscription.check_and_update_status()
        if subscription.is_active:
            return Response({
                'status': 'success',
                'data': {
                    'subscription': SubscriptionSerializer(subscription).data,
                    'message': 'Подписка уже активна'
                },
                'error': None
            })

        # Если уже есть ожидающий платёж с ссылкой — отдаём его, не плодим дубли
        pending_payment = subscription.payments.filter(
            status='pending',
            payment_link__isnull=False
        ).order_by('-created_at').first()

        if pending_payment and pending_payment.payment_link:
            return Response({
                'status': 'success',
                'data': {
                    'payment_link': pending_payment.payment_link,
                    'operation_id': pending_payment.tochka_operation_id,
                    'message': 'Используйте ссылку для оплаты'
                },
                'error': None
            })

        # Создаём новый платёж через Точка Банк
        from .tochka_service import TochkaPaymentService, TochkaAPIError

        payment_link_id = str(_uuid.uuid4())

        try:
            tochka = TochkaPaymentService()
            result = tochka.create_subscription(
                user_id=str(request.user.id),
                user_email=request.user.email,
                payment_link_id=payment_link_id,
            )
        except TochkaAPIError as e:
            logger.error("[Subscription] Ошибка Точки: %s", e)
            return Response({
                'status': 'error',
                'error': f'Ошибка платёжного сервиса: {str(e)}',
                'data': None
            }, status=status.HTTP_502_BAD_GATEWAY)

        # Сохраняем запись о платеже
        SubscriptionPayment.objects.create(
            subscription=subscription,
            amount=Subscription.SUBSCRIPTION_PRICE,
            status='pending',
            payment_provider='tochka',
            external_payment_id=payment_link_id,
            tochka_operation_id=result['operation_id'],
            tochka_consumer_id=result.get('consumer_id', ''),
            payment_link=result['payment_link'],
            tochka_status='Created',
        )

        return Response({
            'status': 'success',
            'data': {
                'payment_link': result['payment_link'],
                'operation_id': result['operation_id'],
                'message': 'Перейдите по ссылке для оплаты'
            },
            'error': None
        })


class TochkaSubscriptionStatusView(APIView):
    """
    Проверить статус оплаты в Точке и активировать подписку если оплачено.

    Вызывается фронтендом после редиректа с оплаты
    (когда Точка возвращает пользователя на /profile?subscription=success).

    GET /api/auth/subscription/check-status/

    Возможные статусы от Точки:
      Active    — оплачено, активируем подписку
      Pending   — ещё не оплачено
      Created   — ещё не оплачено
      Cancelled — отменена
      Inactive  — неактивна
    """
    permission_classes = [IsAuthenticated]
    throttle_classes = [SubscriptionThrottle]

    def get(self, request):
        import logging
        logger = logging.getLogger(__name__)

        if request.user.role != 'worker':
            return Response({
                'status': 'error',
                'error': 'Только для исполнителей'
            }, status=403)

        try:
            subscription = request.user.subscription
        except Subscription.DoesNotExist:
            return Response({
                'status': 'error',
                'error': 'Подписка не найдена'
            }, status=404)

        # Если уже активна — просто возвращаем статус
        subscription.check_and_update_status()
        if subscription.is_active:
            return Response({
                'status': 'success',
                'data': {
                    'subscription': SubscriptionSerializer(subscription).data,
                    'tochka_status': 'Active',
                    'message': 'Подписка активна'
                }
            })

        # Берём последний pending платёж с operation_id
        payment = subscription.payments.filter(
            status='pending',
            tochka_operation_id__isnull=False
        ).order_by('-created_at').first()

        if not payment:
            return Response({
                'status': 'success',
                'data': {
                    'subscription': SubscriptionSerializer(subscription).data,
                    'tochka_status': None,
                    'message': 'Нет ожидающих платежей'
                }
            })

        # Запрашиваем статус в Точке
        from .tochka_service import TochkaPaymentService, TochkaAPIError

        try:
            tochka = TochkaPaymentService()
            tochka_status = tochka.get_subscription_status(payment.tochka_operation_id)
        except TochkaAPIError as e:
            logger.error("[CheckStatus] Ошибка Точки: %s", e)
            return Response({
                'status': 'error',
                'error': f'Не удалось получить статус от Точки: {str(e)}'
            }, status=502)

        # Обновляем tochka_status в любом случае
        payment.tochka_status = tochka_status

        # Активируем подписку при успешной оплате
        if tochka_status in ('Active', 'Paid', 'PAID', 'ACTIVE'):
            payment.status = 'completed'
            payment.save()

            subscription.activate(duration_days=30)
            subscription.refresh_from_db()

            logger.info(
                "[CheckStatus] ✅ Подписка активирована для %s (operation=%s)",
                request.user.email, payment.tochka_operation_id
            )

            return Response({
                'status': 'success',
                'data': {
                    'subscription': SubscriptionSerializer(subscription).data,
                    'tochka_status': tochka_status,
                    'message': 'Подписка успешно активирована!'
                }
            })

        # Отменена или ошибка
        if tochka_status in ('Cancelled', 'CANCELLED', 'Failed', 'FAILED', 'Inactive', 'INACTIVE'):
            payment.status = 'failed'
            payment.save()
        else:
            # Pending / Created — ещё не оплачено
            payment.save()

        return Response({
            'status': 'success',
            'data': {
                'subscription': SubscriptionSerializer(subscription).data,
                'tochka_status': tochka_status,
                'message': 'Оплата ещё не получена. Попробуйте позже.'
            }
        })


# ─── TELEGRAM ────────────────────────────────────────────────────────────────

class TelegramGenerateLinkView(APIView):
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
    permission_classes = [AllowAny]

    def post(self, request):
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
    permission_classes = [AllowAny]

    def post(self, request):
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


# ─── INTERNAL ─────────────────────────────────────────────────────────────────

class InternalUserProfileView(APIView):
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


class InternalSetUserActiveView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def patch(self, request, user_id):
        try:
            user = User.objects.get(id=user_id)

            if user.is_superuser:
                return Response({
                    'status': 'error',
                    'error': 'Нельзя изменить статус суперадмина'
                }, status=403)

            is_active = request.data.get('is_active')
            if is_active is None:
                return Response({
                    'status': 'error',
                    'error': 'Поле is_active обязательно'
                }, status=400)

            user.is_active = bool(is_active)
            user.save(update_fields=['is_active'])

            action = 'разблокирован' if user.is_active else 'заблокирован'
            return Response({
                'status': 'success',
                'data': {
                    'user_id': str(user_id),
                    'is_active': user.is_active,
                    'email': user.email
                },
                'message': f'Пользователь {action}'
            })

        except User.DoesNotExist:
            return Response({
                'status': 'error',
                'error': 'Пользователь не найден'
            }, status=404)
        except Exception as e:
            return Response({
                'status': 'error',
                'error': str(e)
            }, status=400)
class SubscriptionCancelView(APIView):
    """
    Принудительная отмена подписки пользователем.
    Сразу деактивирует подписку и объявления, сигналит в Точку об отмене.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        import os, requests as req
        from .models import Subscription, SubscriptionPayment

        if request.user.role != 'worker':
            return Response({'status': 'error', 'error': 'Только для исполнителей'}, status=403)

        try:
            subscription = request.user.subscription
        except Subscription.DoesNotExist:
            return Response({'status': 'error', 'error': 'Подписка не найдена'}, status=404)

        if not subscription.is_active:
            return Response({'status': 'error', 'error': 'Подписка уже неактивна'}, status=400)

        # 1. Деактивируем подписку у нас
        subscription.deactivate()

        # 2. Деактивируем объявления
        try:
            from .jwt_service import ServiceJWT
            token = ServiceJWT.generate_service_token('auth-cancel', expires_minutes=5)
            market_url = os.getenv('MARKET_SERVICE_URL', 'http://market:8002')
            req.post(
                f"{market_url}/api/market/services/internal-deactivate/",
                headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'},
                json={'owner_id': str(request.user.id)},
                timeout=5
            )
        except Exception as e:
            import logging
            logging.getLogger(__name__).error("[Cancel] Ошибка деактивации объявлений: %s", e)

        # 3. Сигналим Точке об отмене подписки (если есть operationId)
        payment = subscription.payments.filter(
            status='completed',
            tochka_operation_id__isnull=False
        ).order_by('-created_at').first()

        if payment and payment.tochka_operation_id:
            try:
                from .tochka_service import TochkaPaymentService
                tochka = TochkaPaymentService()
                tochka.cancel_subscription(payment.tochka_operation_id)
            except Exception as e:
                import logging
                logging.getLogger(__name__).error("[Cancel] Ошибка отмены в Точке: %s", e)

        return Response({
            'status': 'success',
            'message': 'Подписка отменена. Объявления деактивированы.'
        })
