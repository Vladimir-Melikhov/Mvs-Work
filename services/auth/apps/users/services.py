from typing import Dict, Tuple
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User, Profile, Wallet


class AuthService:
    @staticmethod
    def register_user(email: str, password: str, role: str) -> Tuple[User, Dict[str, str]]:
        """Register new user and return user with tokens"""
        user = User.objects.create_user(email=email, password=password, role=role)
        
        Profile.objects.create(user=user)
        Wallet.objects.create(user=user)
        
        tokens = AuthService._generate_tokens(user)
        return user, tokens

    @staticmethod
    def login_user(email: str, password: str) -> Tuple[User, Dict[str, str]]:
        """Authenticate user and return tokens"""
        user = authenticate(username=email, password=password)
        
        if user is None:
            raise ValueError("Invalid credentials")
        
        if not user.is_active:
            raise ValueError("User is inactive")
        
        tokens = AuthService._generate_tokens(user)
        return user, tokens

    @staticmethod
    def _generate_tokens(user: User) -> Dict[str, str]:
        """Generate JWT tokens"""
        refresh = RefreshToken.for_user(user)
        return {
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        }

    @staticmethod
    def check_balance(user_id: str, amount: float) -> bool:
        """Check if user has enough balance"""
        try:
            wallet = Wallet.objects.get(user_id=user_id)
            return wallet.balance >= amount
        except Wallet.DoesNotExist:
            return False

    @staticmethod
    def hold_funds(user_id: str, amount: float) -> bool:
        """Hold funds from user wallet"""
        try:
            wallet = Wallet.objects.get(user_id=user_id)
            if wallet.balance >= amount:
                wallet.balance -= amount
                wallet.save()
                return True
            return False
        except Wallet.DoesNotExist:
            return False
