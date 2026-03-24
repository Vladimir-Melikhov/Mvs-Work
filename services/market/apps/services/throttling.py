from rest_framework.throttling import UserRateThrottle, AnonRateThrottle


class AIGenerationThrottle(UserRateThrottle):
    scope = 'ai_generation'


class DealCreationThrottle(UserRateThrottle):
    scope = 'deal_creation'


class FileUploadThrottle(UserRateThrottle):
    scope = 'file_upload'


class DealPaymentThrottle(UserRateThrottle):
    scope = 'deal_payment'


class RoomCreationThrottle(UserRateThrottle):
    scope = 'room_creation'


class ServiceCreationThrottle(UserRateThrottle):
    scope = 'service_creation'
