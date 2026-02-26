# services/auth/apps/users/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.utils import timezone
from django.contrib import messages
from .models import (
    User, Profile, Wallet, Subscription, SubscriptionPayment,
    EmailVerification, LoginAttempt, TelegramLinkToken
)


class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name = 'Профиль'
    verbose_name_plural = 'Профиль'
    readonly_fields = ['rating', 'telegram_chat_id', 'created_at', 'updated_at', 'avatar_preview']
    fields = [
        'full_name', 'company_name', 'headline', 'bio',
        'avatar', 'avatar_preview',
        'skills', 'rating',
        'github_link', 'behance_link', 'company_website', 'hourly_rate',
        'telegram_chat_id', 'telegram_notifications_enabled',
        'created_at', 'updated_at',
    ]

    def avatar_preview(self, obj):
        if obj.avatar:
            return format_html('<img src="{}" width="80" height="80" style="border-radius: 50%; object-fit: cover;" />', obj.avatar.url)
        return 'Нет аватара'
    avatar_preview.short_description = 'Превью'


class WalletInline(admin.TabularInline):
    model = Wallet
    can_delete = False
    verbose_name = 'Кошелёк'
    readonly_fields = ['balance', 'created_at', 'updated_at']
    extra = 0


class SubscriptionInline(admin.TabularInline):
    model = Subscription
    can_delete = False
    verbose_name = 'Подписка'
    readonly_fields = ['is_active', 'started_at', 'expires_at', 'created_at']
    extra = 0


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Управление пользователями — главный инструмент администратора"""

    list_display = [
        'email', 'role_badge', 'status_badge',
        'email_verified', 'is_staff',
        'created_at', 'actions_column'
    ]
    list_filter = ['role', 'is_active', 'is_staff', 'is_superuser', 'email_verified', 'created_at']
    search_fields = ['email', 'profile__full_name', 'profile__company_name']
    ordering = ['-created_at']
    actions = ['block_users', 'unblock_users', 'verify_emails', 'make_staff']

    readonly_fields = ['id', 'created_at', 'last_login']

    # Форма редактирования существующего пользователя
    fieldsets = (
        ('Аккаунт', {
            'fields': ('id', 'email', 'password', 'role')
        }),
        ('Статус', {
            'fields': ('is_active', 'email_verified', 'is_staff', 'is_superuser'),
            'description': '⚠️ Блокировка: снимите галочку "Активен"'
        }),
        ('Системная информация', {
            'fields': ('created_at', 'last_login'),
            'classes': ('collapse',)
        }),
    )

    # Форма создания нового пользователя
    add_fieldsets = (
        ('Новый пользователь', {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'role', 'is_active', 'email_verified', 'is_staff'),
        }),
    )

    inlines = [ProfileInline, WalletInline, SubscriptionInline]

    def role_badge(self, obj):
        colors = {
            'client': '#6366f1',
            'worker': '#059669',
            'admin': '#dc2626',
        }
        labels = {
            'client': 'Клиент',
            'worker': 'Исполнитель',
            'admin': 'Администратор',
        }
        color = colors.get(obj.role, '#6b7280')
        label = labels.get(obj.role, obj.role)
        return format_html(
            '<span style="background:{};color:#fff;padding:3px 10px;border-radius:12px;font-size:12px;font-weight:600">{}</span>',
            color, label
        )
    role_badge.short_description = 'Роль'

    def status_badge(self, obj):
        if obj.is_superuser:
            return format_html(
                '<span style="background:#7c3aed;color:#fff;padding:3px 10px;border-radius:12px;font-size:12px;">👑 Суперадмин</span>'
            )
        if not obj.is_active:
            return format_html(
                '<span style="background:#ef4444;color:#fff;padding:3px 10px;border-radius:12px;font-size:12px;">🚫 Заблокирован</span>'
            )
        return format_html(
            '<span style="background:#22c55e;color:#fff;padding:3px 10px;border-radius:12px;font-size:12px;">✓ Активен</span>'
        )
    status_badge.short_description = 'Статус'

    def actions_column(self, obj):
        if obj.is_active and not obj.is_superuser:
            return format_html(
                '<a href="{}/change/" style="color:#ef4444;font-size:12px;">✏️ Редактировать</a>',
                obj.pk
            )
        return format_html('<span style="color:#9ca3af;font-size:12px;">—</span>')
    actions_column.short_description = 'Действия'

    # ─── Групповые действия ───────────────────────────────────────────────────

    @admin.action(description='🚫 Заблокировать выбранных пользователей')
    def block_users(self, request, queryset):
        # Защита: нельзя заблокировать суперюзеров
        protected = queryset.filter(is_superuser=True)
        if protected.exists():
            self.message_user(
                request,
                f'⚠️ Нельзя заблокировать суперадминов: {", ".join(u.email for u in protected)}',
                level=messages.WARNING
            )
            queryset = queryset.filter(is_superuser=False)

        count = queryset.update(is_active=False)
        self.message_user(request, f'✅ Заблокировано {count} пользователей.', level=messages.SUCCESS)

    @admin.action(description='✅ Разблокировать выбранных пользователей')
    def unblock_users(self, request, queryset):
        count = queryset.update(is_active=True)
        self.message_user(request, f'✅ Разблокировано {count} пользователей.', level=messages.SUCCESS)

    @admin.action(description='📧 Подтвердить email выбранных пользователей')
    def verify_emails(self, request, queryset):
        count = queryset.update(email_verified=True)
        self.message_user(request, f'✅ Подтверждён email у {count} пользователей.', level=messages.SUCCESS)

    @admin.action(description='🔑 Дать права staff (доступ к админке)')
    def make_staff(self, request, queryset):
        if not request.user.is_superuser:
            self.message_user(request, '❌ Только суперадмин может выдавать права staff.', level=messages.ERROR)
            return
        count = queryset.update(is_staff=True)
        self.message_user(request, f'✅ Права staff выданы {count} пользователям.', level=messages.SUCCESS)


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ['user_email', 'balance', 'updated_at']
    search_fields = ['user__email']
    readonly_fields = ['user', 'created_at', 'updated_at']
    ordering = ['-balance']

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'Пользователь'

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ['user_email', 'status_badge', 'started_at', 'expires_at']
    list_filter = ['is_active']
    search_fields = ['user__email']
    readonly_fields = ['user', 'created_at', 'updated_at']
    actions = ['activate_subscriptions', 'deactivate_subscriptions']

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'Пользователь'

    def status_badge(self, obj):
        if obj.is_active:
            if obj.expires_at and obj.expires_at < timezone.now():
                return format_html('<span style="color:#f59e0b;font-weight:bold;">⏰ Истекла</span>')
            return format_html('<span style="color:#22c55e;font-weight:bold;">✓ Активна</span>')
        return format_html('<span style="color:#ef4444;">✗ Неактивна</span>')
    status_badge.short_description = 'Статус'

    @admin.action(description='✅ Активировать подписку на 30 дней')
    def activate_subscriptions(self, request, queryset):
        for sub in queryset:
            sub.activate(duration_days=30)
        self.message_user(request, f'✅ Активировано {queryset.count()} подписок.', level=messages.SUCCESS)

    @admin.action(description='🚫 Деактивировать подписки')
    def deactivate_subscriptions(self, request, queryset):
        count = queryset.update(is_active=False)
        self.message_user(request, f'✅ Деактивировано {count} подписок.', level=messages.SUCCESS)


@admin.register(LoginAttempt)
class LoginAttemptAdmin(admin.ModelAdmin):
    list_display = ['email', 'ip_address', 'successful', 'attempt_time']
    list_filter = ['successful', 'attempt_time']
    search_fields = ['email', 'ip_address']
    readonly_fields = ['email', 'ip_address', 'successful', 'attempt_time']
    ordering = ['-attempt_time']

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


# Настройка заголовков
admin.site.site_header = 'MVS-Work — Управление пользователями'
admin.site.site_title = 'MVS Admin'
admin.site.index_title = 'Панель администратора'
