# services/auth/apps/users/throttling.py
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle


class AuthenticationThrottle(AnonRateThrottle):
    """Ограничение для эндпоинтов аутентификации"""
    scope = 'auth'
    rate = '5/minute'  # 5 попыток в минуту


class SubscriptionThrottle(UserRateThrottle):
    """Ограничение для операций с подпиской"""
    scope = 'subscription'
    rate = '10/hour'  # 10 запросов в час


class ProfileUpdateThrottle(UserRateThrottle):
    """Ограничение для обновления профиля"""
    scope = 'profile_update'
    rate = '20/hour'  # 20 обновлений в час


class TelegramLinkThrottle(UserRateThrottle):
    """Ограничение для генерации Telegram ссылок"""
    scope = 'telegram_link'
    rate = '3/hour'  # 3 ссылки в час
