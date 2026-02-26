# services/chat/apps/messaging/authentication.py
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, AuthenticationFailed
from rest_framework_simplejwt.tokens import UntypedToken
from django.conf import settings
import jwt as pyjwt


class RemoteUser:
    """
    Пользователь из JWT токена (пользовательский или межсервисный).
    """
    def __init__(self, token):
        required_fields = ['user_id', 'email', 'role']
        for field in required_fields:
            if field not in token:
                raise AuthenticationFailed(f'Token missing required field: {field}')

        self.id = token.get('user_id')
        self.pk = self.id
        self.email = token.get('email', '')
        self.role = token.get('role', 'client')
        self.is_authenticated = True
        self.is_active = True
        self.is_staff = False
        self.is_superuser = False

        if self.role == 'system':
            self.is_staff = True

    def __str__(self):
        return f"RemoteUser({self.email})"


class RemoteJWTAuthentication(JWTAuthentication):
    """
    Аутентификация через JWT.
    Пробует основной SECRET_KEY, затем SERVICE_JWT_SECRET для межсервисных токенов.
    """

    def get_user(self, validated_token):
        return RemoteUser(validated_token)

    def get_validated_token(self, raw_token):
        """
        Пробуем верифицировать токен двумя ключами:
        1. Основной SECRET_KEY (пользовательские токены от auth service)
        2. SERVICE_JWT_SECRET (межсервисные токены от market/chat)
        """
        # Сначала пробуем стандартный путь (пользовательский JWT)
        try:
            return super().get_validated_token(raw_token)
        except (InvalidToken, Exception):
            pass

        # Затем пробуем service JWT secret
        service_secret = getattr(settings, 'SERVICE_JWT_SECRET', None)
        if not service_secret:
            raise InvalidToken('Token is invalid or expired')

        try:
            decoded = pyjwt.decode(
                raw_token,
                service_secret,
                algorithms=['HS256']
            )

            # Проверяем что это валидный service token
            if decoded.get('type') != 'service':
                raise InvalidToken('Not a service token')

            # Оборачиваем в объект совместимый с DRF simplejwt
            return _ServiceTokenWrapper(decoded)

        except pyjwt.ExpiredSignatureError:
            raise InvalidToken('Service token has expired')
        except pyjwt.InvalidTokenError as e:
            raise InvalidToken(f'Service token invalid: {e}')


class _ServiceTokenWrapper:
    """
    Лёгкая обёртка над decoded payload сервисного токена,
    совместимая с интерфейсом simplejwt validated_token.
    """
    def __init__(self, payload: dict):
        self._payload = payload

    def __getitem__(self, key):
        return self._payload[key]

    def __contains__(self, key):
        return key in self._payload

    def get(self, key, default=None):
        return self._payload.get(key, default)
