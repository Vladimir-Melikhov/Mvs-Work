from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, AuthenticationFailed

class RemoteUser:
    """
    Класс-заглушка, имитирующий пользователя Django.
    Он не хранится в БД, а создается на лету из данных токена.
    """
    def __init__(self, token):
        self.id = token.get('user_id')
        self.pk = self.id  # Django часто использует pk вместо id
        self.email = token.get('email', '')
        self.role = token.get('role', 'client')
        self.is_authenticated = True
        self.is_active = True
        self.is_staff = False
        self.is_superuser = False
        
        # ✅ Поддержка системного пользователя
        if self.role == 'system':
            self.is_system = True
        else:
            self.is_system = False

    def __str__(self):
        return f"RemoteUser({self.email})"


class StatelessJWTAuthentication(JWTAuthentication):
    """
    Кастомная аутентификация: проверяет подпись токена, 
    но НЕ лезет в базу данных за пользователем.
    """
    def get_user(self, validated_token):
        try:
            # Вместо похода в БД, просто возвращаем объект RemoteUser с данными из токена
            return RemoteUser(validated_token)
        except Exception as e:
            raise AuthenticationFailed('Error creating user from token')
