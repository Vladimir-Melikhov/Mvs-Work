from channels.middleware import BaseMiddleware
from channels.db import database_sync_to_async
from rest_framework_simplejwt.tokens import UntypedToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from django.contrib.auth.models import AnonymousUser
from urllib.parse import parse_qs
from .models import Room


class RemoteUser:
    """Пользователь из JWT токена"""
    def __init__(self, user_id, email, role):
        self.id = user_id
        self.pk = user_id
        self.email = email
        self.role = role
        self.is_authenticated = True
        self.is_active = True


class JWTAuthMiddleware(BaseMiddleware):
    """JWT аутентификация для WebSocket"""
    
    async def __call__(self, scope, receive, send):
        query_string = scope.get('query_string', b'').decode()
        params = parse_qs(query_string)
        token = params.get('token', [None])[0]
        
        if token:
            try:
                # Валидация токена
                validated_token = UntypedToken(token)
                
                # Извлекаем данные пользователя
                user_id = validated_token.get('user_id')
                email = validated_token.get('email', '')
                role = validated_token.get('role', 'client')
                
                if user_id:
                    scope['user'] = RemoteUser(user_id, email, role)
                else:
                    scope['user'] = AnonymousUser()
                    
            except (InvalidToken, TokenError) as e:
                scope['user'] = AnonymousUser()
        else:
            scope['user'] = AnonymousUser()
        
        return await super().__call__(scope, receive, send)
    