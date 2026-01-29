from rest_framework.throttling import UserRateThrottle


class AIGenerationThrottle(UserRateThrottle):
    """Ограничение для генерации AI ТЗ (дорогая операция)"""
    scope = 'ai_generation'


class DealCreationThrottle(UserRateThrottle):
    """Ограничение для создания сделок"""
    scope = 'deal_creation'


class FileUploadThrottle(UserRateThrottle):
    """Ограничение для загрузки файлов"""
    scope = 'file_upload'
