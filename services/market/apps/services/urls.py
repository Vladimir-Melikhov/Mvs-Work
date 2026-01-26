from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ServiceViewSet, DealViewSet, ReviewViewSet, UpdateOwnerAvatarView

router = DefaultRouter()
router.register('services', ServiceViewSet, basename='service')
router.register('deals', DealViewSet, basename='deal')
router.register('reviews', ReviewViewSet, basename='review')

urlpatterns = [
    path('services/update-owner-avatar/', UpdateOwnerAvatarView.as_view(), name='update-owner-avatar'),
    path('', include(router.urls)),
]