from django.urls import path, include

urlpatterns = [
    path('api/market/', include('apps.services.urls')),
]