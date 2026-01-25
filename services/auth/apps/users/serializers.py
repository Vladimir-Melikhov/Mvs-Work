from rest_framework import serializers
from .models import User, Profile, Wallet, Subscription, SubscriptionPayment
from django.core.files.uploadedfile import InMemoryUploadedFile
import os


class SubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscription
        fields = ['id', 'is_active', 'started_at', 'expires_at', 'created_at']
        read_only_fields = ['id', 'created_at']


class ProfileSerializer(serializers.ModelSerializer):
    avatar = serializers.ImageField(required=False, allow_null=True)
    avatar_url = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = Profile
        fields = [
            'full_name',
            'company_name', 
            'headline', 
            'company_website', 
            'hourly_rate',
            'avatar',
            'avatar_url',
            'bio', 
            'skills', 
            'rating',
            'github_link',
            'behance_link',
        ]
        read_only_fields = ['rating', 'avatar_url']
    
    def get_avatar_url(self, obj):
        """Возвращает полный URL аватарки"""
        if obj.avatar:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.avatar.url)
            return obj.avatar.url
        return None
    
    def validate_avatar(self, value):
        """Валидация загружаемого файла"""
        if value is None:
            return value
            
        if not isinstance(value, InMemoryUploadedFile):
            return value
        
        ext = os.path.splitext(value.name)[1][1:].lower()
        allowed_extensions = ['jpg', 'jpeg', 'png', 'gif', 'webp']
        
        if ext not in allowed_extensions:
            raise serializers.ValidationError(
                f"Неподдерживаемый формат файла. Разрешены: {', '.join(allowed_extensions)}"
            )
        
        if value.size > 5 * 1024 * 1024:
            raise serializers.ValidationError(
                "Размер файла не должен превышать 5MB"
            )
        
        return value
    
    def update(self, instance, validated_data):
        """Обновление профиля с обработкой аватарки"""
        if 'avatar' in validated_data and validated_data['avatar']:
            if instance.avatar:
                instance.avatar.delete(save=False)
        
        return super().update(instance, validated_data)


class WalletSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wallet
        fields = ['balance']


class UserSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(read_only=True)
    wallet = WalletSerializer(read_only=True)
    subscription = SubscriptionSerializer(read_only=True)

    class Meta:
        model = User
        fields = ['id', 'email', 'role', 'profile', 'wallet', 'subscription', 'created_at']
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
