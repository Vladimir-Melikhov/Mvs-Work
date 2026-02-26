# services/auth/config/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# Auth admin живёт по /auth-admin/ (Caddy проксирует /auth-admin* → auth:8001)
# Но Django внутри слушает просто /auth-admin/
admin.site.site_url = '/auth-admin/'

urlpatterns = [
    path('auth-admin/', admin.site.urls),
    path('api/auth/', include('apps.users.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)