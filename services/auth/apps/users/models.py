import uuid
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.core.files.storage import FileSystemStorage
from django.utils import timezone
from datetime import timedelta
import os


avatar_storage = FileSystemStorage(location='media/avatars')


def avatar_upload_path(instance, filename):
    """Генерирует путь для загрузки аватарки"""
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    return os.path.join('avatars', filename)


class UserManager(BaseUserManager):
    def create_user(self, email: str, password: str, **extra_fields):
        if not email:
            raise ValueError('Email is required')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user


class User(AbstractBaseUser):
    ROLE_CHOICES = [
        ('client', 'Client'),
        ('worker', 'Worker'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True, db_index=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='client')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        db_table = 'users'
        ordering = ['-created_at']

    def __str__(self) -> str:
        return self.email


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    full_name = models.CharField(max_length=100, blank=True, null=True)
    company_name = models.CharField(max_length=255, blank=True, null=True)
    headline = models.CharField(max_length=255, blank=True, null=True)
    company_website = models.URLField(blank=True, null=True)
    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    avatar = models.ImageField(
        upload_to=avatar_upload_path,
        blank=True,
        null=True,
        max_length=500,
        help_text="Аватар пользователя (JPG, PNG, GIF до 5MB)"
    )
    
    bio = models.TextField(blank=True, null=True)
    skills = models.JSONField(default=list, blank=True)
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    github_link = models.URLField(blank=True, null=True, help_text="Ссылка на GitHub профиль")
    behance_link = models.URLField(blank=True, null=True, help_text="Ссылка на Behance профиль")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'profiles'

    def __str__(self) -> str:
        return f"Profile of {self.user.email}"
    
    def get_avatar_url(self):
        """Возвращает URL аватарки или None"""
        if self.avatar:
            return self.avatar.url
        return None


class Wallet(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='wallet')
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'wallets'

    def __str__(self) -> str:
        return f"Wallet of {self.user.email}: ${self.balance}"


class Subscription(models.Model):
    """Модель подписки для воркеров"""
    SUBSCRIPTION_PRICE = 444.00
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='subscription')
    is_active = models.BooleanField(default=False, db_index=True)
    started_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'subscriptions'
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f"Subscription of {self.user.email} - {'Active' if self.is_active else 'Inactive'}"

    def activate(self, duration_days=30):
        """Активировать подписку на указанное количество дней"""
        self.is_active = True
        self.started_at = timezone.now()
        self.expires_at = timezone.now() + timedelta(days=duration_days)
        self.save()

    def deactivate(self):
        """Деактивировать подписку"""
        self.is_active = False
        self.save()

    def is_expired(self):
        """Проверить истекла ли подписка"""
        if not self.expires_at:
            return True
        return timezone.now() > self.expires_at

    def check_and_update_status(self):
        """Проверить и обновить статус подписки если истекла"""
        if self.is_active and self.is_expired():
            self.deactivate()
            return True
        return False


class SubscriptionPayment(models.Model):
    """История платежей за подписку"""
    STATUS_CHOICES = [
        ('pending', 'Ожидает оплаты'),
        ('completed', 'Оплачено'),
        ('failed', 'Ошибка'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=Subscription.SUBSCRIPTION_PRICE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_provider = models.CharField(max_length=50, default='stub')
    external_payment_id = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'subscription_payments'
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f"Payment {self.id} - {self.status}"


# ✅ НОВАЯ МОДЕЛЬ: Импорт Service из market (для типизации)
# ВАЖНО: Это НЕ настоящая модель, а proxy для типизации
class Service:
    """Proxy-модель для обновления объявлений через API"""
    pass
