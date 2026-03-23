# services/market/apps/services/throttling.py
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle


class AIGenerationThrottle(UserRateThrottle):
    """Ограничение для генерации AI ТЗ (дорогая операция) — 5/час"""
    scope = 'ai_generation'


class DealCreationThrottle(UserRateThrottle):
    """Ограничение для создания сделок — 10/час"""
    scope = 'deal_creation'


class FileUploadThrottle(UserRateThrottle):
    """Ограничение для загрузки файлов — 50/час"""
    scope = 'file_upload'


class DealPaymentThrottle(UserRateThrottle):
    """Ограничение для оплаты сделок — 10/час"""
    scope = 'deal_payment'


class RoomCreationThrottle(UserRateThrottle):
    """Ограничение для создания комнат — 20/час"""
    scope = 'room_creation'


class ServiceCreationThrottle(UserRateThrottle):
    """Ограничение для создания объявлений — 1 раз в 3 часа"""
    scope = 'service_creation'

    def parse_rate(self, rate):
        return (3, 10800)