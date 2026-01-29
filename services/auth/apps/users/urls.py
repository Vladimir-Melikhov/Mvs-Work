from django.urls import path
from .views import (
    RegisterView, 
    LoginView, 
    ProfileView, 
    CheckBalanceView, 
    BatchUsersView, 
    PublicProfileView,
    SubscriptionView,
    TelegramGenerateLinkView,
    TelegramVerifyTokenView,
    TelegramDisconnectView,
    TelegramGetUserByIdView,
)
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('check-balance/', CheckBalanceView.as_view(), name='check_balance'),
    path('users/batch/', BatchUsersView.as_view(), name='users_batch'),
    path('users/<uuid:user_id>/', PublicProfileView.as_view(), name='public_profile'),
    path('subscription/', SubscriptionView.as_view(), name='subscription'),
    path('internal/users/<uuid:user_id>/profile/', views.InternalUserProfileView.as_view(), name='internal-user-profile'),
    path('telegram/generate-link/', TelegramGenerateLinkView.as_view(), name='telegram_generate_link'),
    path('telegram/verify-token/', TelegramVerifyTokenView.as_view(), name='telegram_verify_token'),
    path('telegram/disconnect/', TelegramDisconnectView.as_view(), name='telegram_disconnect'),
    path('telegram/get-user/', TelegramGetUserByIdView.as_view(), name='telegram_get_user'),
]
