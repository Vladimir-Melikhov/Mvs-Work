import jwt
import os
from datetime import datetime, timedelta
from django.conf import settings

class ServiceJWT:
    """JWT для межсервисного взаимодействия"""
    
    SECRET_KEY = os.getenv('SERVICE_JWT_SECRET', settings.SECRET_KEY + '-service-jwt')
    ALGORITHM = 'HS256'
    
    @classmethod
    def generate_service_token(cls, service_name, expires_minutes=60):
        """Генерация токена для сервиса"""
        payload = {
            'service': service_name,
            'exp': datetime.utcnow() + timedelta(minutes=expires_minutes),
            'iat': datetime.utcnow(),
            'type': 'service'
        }
        return jwt.encode(payload, cls.SECRET_KEY, algorithm=cls.ALGORITHM)
