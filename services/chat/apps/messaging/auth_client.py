import os
import requests
from .jwt_service import ServiceJWT

class AuthServiceClient:
    """Клиент для запросов к Auth Service с JWT аутентификацией"""
    
    def __init__(self):
        self.base_url = os.getenv('AUTH_SERVICE_URL', 'http://localhost:8001')
        self.service_name = 'chat-service'
    
    def _get_headers(self):
        """Получить headers с JWT токеном"""
        token = ServiceJWT.generate_service_token(self.service_name)
        return {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
    
    def get_user_profile(self, user_id):
        """Получить профиль пользователя"""
        try:
            response = requests.get(
                f"{self.base_url}/api/auth/internal/users/{user_id}/profile/",
                headers=self._get_headers(),
                timeout=5
            )
            
            if response.status_code == 200:
                return response.json().get('data')
            
            print(f"[AuthClient] Ошибка: {response.status_code} - {response.text}")
            return None
        except Exception as e:
            print(f"[AuthClient] Исключение: {e}")
            return None
