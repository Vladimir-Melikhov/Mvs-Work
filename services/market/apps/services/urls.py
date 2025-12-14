from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ServiceViewSet, OrderViewSet

router = DefaultRouter()
router.register('services', ServiceViewSet, basename='service')
router.register('orders', OrderViewSet, basename='order')

urlpatterns = [
    path('', include(router.urls)),
]