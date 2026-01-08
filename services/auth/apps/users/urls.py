from django.urls import path
from .views import RegisterView, LoginView, ProfileView, CheckBalanceView, BatchUsersView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('check-balance/', CheckBalanceView.as_view(), name='check_balance'),
    path('users/batch/', BatchUsersView.as_view(), name='users_batch'),
]