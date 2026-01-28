import uuid
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.core.files.storage import FileSystemStorage
from django.utils import timezone
from datetime import timedelta
import os
from django.core.exceptions import ValidationError
import bleach

avatar_storage = FileSystemStorage(location='media/avatars')


def validate_skills(value):
    """Валидация навыков с sanitization"""
    if not isinstance(value, list):
        raise ValidationError('Skills должны быть списком')
    
    if len(value) > 50:
        raise ValidationError('Максимум 50 навыков')
    
    cleaned_skills = []
    for skill in value:
        if not isinstance(skill, str):
            raise ValidationError('Каждый навык должен быть строкой')
        
        # Sanitization - удаляем HTML теги и опасные символы
        clean_skill = bleach.clean(skill, tags=[], strip=True)
        clean_skill = clean_skill.strip()
        
        if len(clean_skill) > 100:
            raise ValidationError('Навык не может быть длиннее 100 символов')
        
        if not clean_skill:
            continue
        
        # Проверка на SQL-инъекции
        dangerous_patterns = ['--', '/*', '*/', 'DROP', 'SELECT', 'INSERT', 'UPDATE', 'DELETE', 'UNION']
        if any(pattern.lower() in clean_skill.lower() for pattern in dangerous_patterns):
            raise ValidationError(f'Навык содержит недопустимые символы: {skill}')
        
        cleaned_skills.append(clean_skill)
    
    # Возвращаем очищенный список
    return cleaned_skills


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
    
    telegram_chat_id = models.BigIntegerField(
        null=True, 
        blank=True, 
        unique=True,
        help_text="Telegram Chat ID для уведомлений"
    )
    telegram_notifications_enabled = models.BooleanField(
        default=False,
        help_text="Включены ли Telegram уведомления"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'profiles'

    def __str__(self) -> str:
        return f"Profile of {self.user.email}"
    
    def clean(self):
        """Валидация и sanitization при сохранении"""
        super().clean()
        
        # Sanitize text fields
        if self.bio:
            self.bio = bleach.clean(self.bio, tags=[], strip=True)
        
        if self.full_name:
            self.full_name = bleach.clean(self.full_name, tags=[], strip=True)
        
        if self.company_name:
            self.company_name = bleach.clean(self.company_name, tags=[], strip=True)
        
        if self.headline:
            self.headline = bleach.clean(self.headline, tags=[], strip=True)
        
        # Валидация и очистка навыков
        if self.skills:
            self.skills = validate_skills(self.skills)
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
    
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


class TelegramLinkToken(models.Model):
    """Одноразовые токены для привязки Telegram аккаунта"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='telegram_tokens')
    token = models.CharField(max_length=64, unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'telegram_link_tokens'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Token for {self.user.email} - {'Used' if self.used else 'Active'}"
    
    def is_expired(self):
        return timezone.now() > self.expires_at
    
    def is_valid(self):
        return not self.used and not self.is_expired()


class Service:
    """Proxy-модель для обновления объявлений через API"""
    pass
