import jwt
import os
from datetime import datetime, timedelta
from django.conf import settings

class ServiceJWT:
    """JWT для межсервисного взаимодействия с отдельным секретом"""
    
    # Отдельный секрет для межсервисных токенов
    SECRET_KEY = os.getenv('SERVICE_JWT_SECRET', settings.SECRET_KEY + '-service-jwt-secure')
    ALGORITHM = 'HS256'
    
    @classmethod
    def generate_service_token(cls, service_name, expires_minutes=5):
        """Генерация токена для сервиса с коротким временем жизни"""
        payload = {
            'service': service_name,
            'role': 'system',
            'type': 'service',
            'user_id': '00000000-0000-0000-0000-000000000000',
            'email': f'system@{service_name}.internal',
            'exp': datetime.utcnow() + timedelta(minutes=expires_minutes),
            'iat': datetime.utcnow(),
        }
        return jwt.encode(payload, cls.SECRET_KEY, algorithm=cls.ALGORITHM)
    
    @classmethod
    def verify_service_token(cls, token):
        """Проверка токена"""
        try:
            payload = jwt.decode(token, cls.SECRET_KEY, algorithms=[cls.ALGORITHM])
            
            # Проверяем что это service токен
            if payload.get('type') != 'service':
                return None
            
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
