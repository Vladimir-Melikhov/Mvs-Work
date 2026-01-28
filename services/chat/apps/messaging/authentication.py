from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, AuthenticationFailed
import jwt as pyjwt


class RemoteUser:
    """
    Класс-заглушка, имитирующий пользователя Django.
    Он не хранится в БД, а создается на лету из данных токена.
    """
    def __init__(self, token):
        # Валидация токена
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
    Аутентификация через JWT токен от Auth Service.
    Не обращается к локальной БД, создает RemoteUser из токена.
    """
    def get_user(self, validated_token):
        return RemoteUser(validated_token)
