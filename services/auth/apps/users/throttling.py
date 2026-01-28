from rest_framework.throttling import UserRateThrottle, AnonRateThrottle


class AuthenticationThrottle(AnonRateThrottle):
    """Ограничение для эндпоинтов аутентификации"""
    scope = 'auth'


class SubscriptionThrottle(UserRateThrottle):
    """Ограничение для операций с подпиской"""
    scope = 'subscription'
