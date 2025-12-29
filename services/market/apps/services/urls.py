from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ServiceViewSet, DealViewSet

router = DefaultRouter()
router.register('services', ServiceViewSet, basename='service')
router.register('deals', DealViewSet, basename='deal')

urlpatterns = [
    path('', include(router.urls)),
]
