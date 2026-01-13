from django.contrib import admin  # Добавь этот импорт
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),  # Добавь эту строку
    path('api/market/', include('apps.services.urls')),
]
