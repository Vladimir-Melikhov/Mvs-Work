from rest_framework import serializers
from .models import User, Profile, Wallet


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = [
            'full_name',       # <-- Было display_name
            'company_name', 
            'headline', 
            'company_website', 
            'hourly_rate',
            'avatar', 
            'bio', 
            'skills', 
            'rating'
        ]
        read_only_fields = ['rating']


class WalletSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wallet
        fields = ['balance']


class UserSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(read_only=True)
    wallet = WalletSerializer(read_only=True)

    class Meta:
        model = User
        fields = ['id', 'email', 'role', 'profile', 'wallet', 'created_at']
        read_only_fields = ['id', 'created_at']


class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=6)
    role = serializers.ChoiceField(choices=['client', 'worker'], default='client')

    def validate_email(self, value: str) -> str:
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already exists")
        return value


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)