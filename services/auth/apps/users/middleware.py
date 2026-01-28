from django.http import JsonResponse
from .jwt_service import ServiceJWT

class InternalServiceMiddleware:
    """Middleware для проверки JWT токенов внутренних сервисов"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Проверяем только internal эндпоинты
        if request.path.startswith('/api/auth/internal/'):
            auth_header = request.headers.get('Authorization')
            
            if not auth_header or not auth_header.startswith('Bearer '):
                return JsonResponse({
                    'status': 'error',
                    'error': 'Missing or invalid authorization header'
                }, status=403)
            
            token = auth_header.replace('Bearer ', '')
            payload = ServiceJWT.verify_service_token(token)
            
            if not payload:
                return JsonResponse({
                    'status': 'error',
                    'error': 'Invalid or expired service token'
                }, status=403)
            
            # Сохраняем информацию о сервисе в request
            request.service_name = payload.get('service')
        
        return self.get_response(request)
