# services/market/apps/services/throttling.py
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle


class AIGenerationThrottle(UserRateThrottle):
    """Ограничение для генерации AI ТЗ (дорогая операция)"""
    scope = 'ai_generation'


class DealCreationThrottle(UserRateThrottle):
    """Ограничение для создания сделок"""
    scope = 'deal_creation'


class FileUploadThrottle(UserRateThrottle):
    """Ограничение для загрузки файлов"""
    scope = 'file_upload'


class DealPaymentThrottle(UserRateThrottle):
    """✅ Ограничение для оплаты сделок"""
    scope = 'deal_payment'


class RoomCreationThrottle(UserRateThrottle):
    """✅ Ограничение для создания комнат"""
    scope = 'room_creation'
