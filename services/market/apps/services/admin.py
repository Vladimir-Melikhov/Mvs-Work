# services/market/apps/services/admin.py
import uuid
import os
import requests
from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.contrib import messages
from .models import Service, ServiceImage, Deal, Transaction, Review, Favorite
from .deal_service import DealService


# ─── Вспомогательные функции ─────────────────────────────────────────────────

def _get_admin_token():
    """
    Получаем системный JWT-токен для вызовов к auth service.
    Используем ServiceJWT — не зависим от логина/пароля.
    """
    from .jwt_service import ServiceJWT
    return ServiceJWT.generate_service_token('market-admin', expires_minutes=10)


def _block_user_in_auth(user_id: str, block: bool) -> bool:
    """
    Блокировка/разблокировка пользователя через Auth Service API.
    Возвращает True при успехе.
    """
    auth_url = os.getenv('AUTH_SERVICE_URL', 'http://auth:8001')
    token = _get_admin_token()

    try:
        response = requests.patch(
            f"{auth_url}/api/auth/internal/users/{user_id}/set-active/",
            headers={
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            },
            json={'is_active': not block},
            timeout=5
        )
        return response.status_code == 200
    except Exception as e:
        print(f"[Admin] Ошибка запроса к auth service: {e}")
        return False


# ─── Service (объявления) ─────────────────────────────────────────────────────

class ServiceImageInline(admin.TabularInline):
    model = ServiceImage
    extra = 0
    readonly_fields = ['image_preview', 'created_at']
    fields = ['image', 'image_preview', 'order', 'created_at']

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" width="80" height="60" style="object-fit:cover;border-radius:6px;" />',
                obj.image.url
            )
        return '—'
    image_preview.short_description = 'Превью'


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'category_badge', 'price_formatted',
        'owner_name', 'active_badge', 'created_at'
    ]
    list_filter = ['category', 'is_active', 'created_at']
    search_fields = ['title', 'description', 'owner_name', 'owner_id']
    readonly_fields = ['id', 'owner_id', 'created_at', 'updated_at']
    actions = ['activate_services', 'deactivate_services', 'delete_selected_services']
    inlines = [ServiceImageInline]

    fieldsets = (
        ('Основная информация', {
            'fields': ('id', 'title', 'description', 'price', 'category', 'subcategory', 'tags')
        }),
        ('Публикация', {
            'fields': ('is_active',),
        }),
        ('Владелец', {
            'fields': ('owner_id', 'owner_name', 'owner_avatar'),
            'classes': ('collapse',)
        }),
        ('AI шаблон', {
            'fields': ('ai_template',),
            'classes': ('collapse',)
        }),
        ('Метаданные', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def category_badge(self, obj):
        colors = {
            'development': '#6366f1', 'design': '#ec4899',
            'marketing': '#f59e0b', 'writing': '#10b981',
            'video': '#ef4444', 'audio': '#8b5cf6',
            'business': '#0ea5e9', 'other': '#6b7280',
        }
        color = colors.get(obj.category, '#6b7280')
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 8px;border-radius:10px;font-size:11px">{}</span>',
            color, obj.get_category_display()
        )
    category_badge.short_description = 'Категория'

    def price_formatted(self, obj):
        return format_html('<b style="color:#059669">{} ₽</b>', int(obj.price))
    price_formatted.short_description = 'Цена'
    price_formatted.admin_order_field = 'price'

    def active_badge(self, obj):
        if obj.is_active:
            return format_html('<span style="color:#22c55e;font-weight:bold">✓ Активно</span>')
        return format_html('<span style="color:#9ca3af">✗ Скрыто</span>')
    active_badge.short_description = 'Статус'
    active_badge.admin_order_field = 'is_active'

    @admin.action(description='✅ Активировать объявления')
    def activate_services(self, request, queryset):
        count = queryset.update(is_active=True)
        self.message_user(request, f'✅ Активировано {count} объявлений.', level=messages.SUCCESS)

    @admin.action(description='🚫 Деактивировать объявления')
    def deactivate_services(self, request, queryset):
        count = queryset.update(is_active=False)
        self.message_user(request, f'✅ Деактивировано {count} объявлений.', level=messages.SUCCESS)

    @admin.action(description='🗑️ Удалить выбранные объявления')
    def delete_selected_services(self, request, queryset):
        count = queryset.count()
        queryset.delete()
        self.message_user(request, f'✅ Удалено {count} объявлений.', level=messages.SUCCESS)

    # Разрешаем удаление через стандартный механизм
    def has_delete_permission(self, request, obj=None):
        return True


# ─── Deal (заказы / арбитраж) ─────────────────────────────────────────────────

@admin.register(Deal)
class DealAdmin(admin.ModelAdmin):
    list_display = [
        'id_short',
        'title',
        'status_badge',
        'price_formatted',
        'dispute_status',
        'created_at'
    ]
    list_filter = ['status', 'created_at', 'dispute_winner']
    search_fields = ['title', 'client_id', 'worker_id', 'id']

    readonly_fields = [
        'id', 'chat_room_id',
        'client_id', 'worker_id',
        'service', 'title', 'description', 'price', 'status',
        'revision_count', 'max_revisions', 'was_delivered',
        'delivery_message', 'completion_message', 'cancellation_reason',
        'dispute_info_panel',
        'dispute_client_reason', 'dispute_worker_defense',
        'dispute_created_at', 'dispute_resolved_at', 'dispute_winner',
        'created_at', 'paid_at', 'delivered_at', 'completed_at', 'cancelled_at',
    ]

    fieldsets = (
        ('🔥 АРБИТРАЖ', {
            'fields': ('dispute_info_panel',),
            'description': 'Используйте групповые действия для разрешения споров'
        }),
        ('Основная информация', {
            'fields': ('id', 'title', 'price', 'status', 'was_delivered'),
            'classes': ('collapse',)
        }),
        ('Участники', {
            'fields': ('client_id', 'worker_id'),
            'classes': ('collapse',)
        }),
        ('Тексты', {
            'fields': ('description', 'delivery_message', 'completion_message', 'cancellation_reason'),
            'classes': ('collapse',)
        }),
        ('Временные метки', {
            'fields': ('created_at', 'paid_at', 'delivered_at', 'completed_at', 'cancelled_at'),
            'classes': ('collapse',)
        }),
    )

    actions = ['resolve_dispute_client', 'resolve_dispute_worker']

    # ─── Колонки ──────────────────────────────────────────────────────────────

    def id_short(self, obj):
        return str(obj.id)[:8] + '…'
    id_short.short_description = 'ID'

    def price_formatted(self, obj):
        return format_html('<b>{} ₽</b>', int(obj.price))
    price_formatted.short_description = 'Сумма'
    price_formatted.admin_order_field = 'price'

    def status_badge(self, obj):
        colors = {
            'pending': '#9333ea', 'paid': '#3b82f6',
            'delivered': '#22c55e', 'dispute': '#ef4444',
            'completed': '#f97316', 'cancelled': '#6b7280',
        }
        labels = {
            'pending': 'Ожидает', 'paid': 'В работе',
            'delivered': 'На проверке', 'dispute': '⚠️ СПОР',
            'completed': 'Завершён', 'cancelled': 'Отменён',
        }
        color = colors.get(obj.status, '#6b7280')
        label = labels.get(obj.status, obj.status)
        return format_html(
            '<span style="background:{};color:#fff;padding:4px 10px;border-radius:8px;font-weight:600;font-size:12px">{}</span>',
            color, label
        )
    status_badge.short_description = 'Статус'

    def dispute_status(self, obj):
        if obj.status != 'dispute' and not obj.dispute_winner:
            return '—'
        if obj.dispute_winner:
            label = '✅ Клиент' if obj.dispute_winner == 'client' else '✅ Исполнитель'
            color = '#22c55e'
            return format_html(
                '<span style="background:{};color:#fff;padding:3px 8px;border-radius:8px;font-size:11px">{}</span>',
                color, label
            )
        if not obj.dispute_worker_defense:
            return format_html('<span style="color:#f59e0b;font-weight:600">⏳ Ждёт ответа</span>')
        return format_html('<span style="color:#ef4444;font-weight:700">⚡ ТРЕБУЕТ РЕШЕНИЯ</span>')
    dispute_status.short_description = 'Спор'

    def dispute_info_panel(self, obj):
        """Информационная панель спора — всё в одном месте"""
        if obj.status != 'dispute' and not obj.dispute_winner:
            return format_html('<p style="color:#9ca3af">Заказ не в споре</p>')

        sections = []

        # Заголовок
        if obj.dispute_winner:
            w = 'КЛИЕНТ' if obj.dispute_winner == 'client' else 'ИСПОЛНИТЕЛЬ'
            color = '#22c55e'
            sections.append(f'<div style="background:{color};color:#fff;padding:12px 16px;border-radius:8px;font-size:16px;font-weight:700;text-align:center;margin-bottom:16px">✅ РАЗРЕШЁН В ПОЛЬЗУ: {w}</div>')
        elif obj.dispute_worker_defense:
            sections.append('<div style="background:#ef4444;color:#fff;padding:12px 16px;border-radius:8px;font-size:16px;font-weight:700;text-align:center;margin-bottom:16px">⚡ ТРЕБУЕТ РЕШЕНИЯ АДМИНИСТРАТОРА</div>')
        else:
            sections.append('<div style="background:#f59e0b;color:#fff;padding:12px 16px;border-radius:8px;font-size:15px;font-weight:600;text-align:center;margin-bottom:16px">⏳ Ожидаем ответ исполнителя</div>')

        # Мета
        sections.append(f'<div style="background:#f3f4f6;padding:12px;border-radius:8px;margin-bottom:12px"><b>📋 Заказ:</b> {obj.title}<br><b>💰 Сумма:</b> {int(obj.price)} ₽</div>')

        # ТЗ
        sections.append(f'<div style="border:2px solid #e5e7eb;padding:12px;border-radius:8px;margin-bottom:12px"><div style="font-weight:700;margin-bottom:6px">📝 Техническое задание</div><div style="color:#4b5563;white-space:pre-wrap;max-height:150px;overflow-y:auto">{obj.description}</div></div>')

        # Результат работы + прикреплённые файлы
        delivery_text = obj.delivery_message or ''
        attachments = obj.delivery_attachments.all()
        has_delivery = bool(delivery_text) or attachments.exists()

        if has_delivery:
            attachments_html = ''
            if attachments.exists():
                attachments_html += '<div style="margin-top:10px;padding-top:10px;border-top:1px solid #d1fae5"><div style="font-size:12px;font-weight:700;color:#065f46;margin-bottom:6px;text-transform:uppercase;letter-spacing:0.05em">📎 Прикреплённые файлы</div>'
                for att in attachments:
                    if att.file:
                        file_url = att.file.url
                        file_size_kb = round(att.file_size / 1024, 1)
                        attachments_html += (
                            f'<div style="margin-bottom:6px">'
                            f'<a href="{file_url}" target="_blank" download="{att.filename}" '
                            f'style="display:inline-flex;align-items:center;gap:8px;padding:7px 14px;'
                            f'background:#f0fdf4;border:1px solid #86efac;border-radius:8px;'
                            f'color:#15803d;text-decoration:none;font-size:12px;font-weight:600;'
                            f'transition:background 0.2s;">'
                            f'⬇️ {att.filename}'
                            f'<span style="color:#6b7280;font-weight:400;">({file_size_kb} KB)</span>'
                            f'</a>'
                            f'</div>'
                        )
                attachments_html += '</div>'

            sections.append(
                f'<div style="border:2px solid #10b981;padding:12px;border-radius:8px;margin-bottom:12px">'
                f'<div style="font-weight:700;color:#059669;margin-bottom:6px">📦 Результат работы</div>'
                f'<div style="white-space:pre-wrap;max-height:120px;overflow-y:auto;color:#1a1a2e">{delivery_text}</div>'
                f'{attachments_html}'
                f'</div>'
            )

        # Претензия
        sections.append(f'<div style="background:#fee2e2;border:2px solid #fca5a5;padding:12px;border-radius:8px;margin-bottom:12px"><div style="font-weight:700;color:#dc2626;margin-bottom:6px">👤 Претензия клиента</div><div style="color:#7f1d1d;white-space:pre-wrap">{obj.dispute_client_reason or "—"}</div></div>')

        # Защита
        if obj.dispute_worker_defense:
            sections.append(f'<div style="background:#dbeafe;border:2px solid #93c5fd;padding:12px;border-radius:8px;margin-bottom:12px"><div style="font-weight:700;color:#1d4ed8;margin-bottom:6px">🛡️ Защита исполнителя</div><div style="color:#1e3a8a;white-space:pre-wrap">{obj.dispute_worker_defense}</div></div>')

        # Инструкция
        if not obj.dispute_winner and obj.dispute_worker_defense:
            sections.append('<div style="background:#fef3c7;border:2px solid #fbbf24;padding:12px;border-radius:8px;text-align:center;color:#92400e"><b>Как разрешить:</b> выберите заказ галочкой → Действие → «Разрешить в пользу...» → Выполнить</div>')

        return mark_safe('<div style="font-family:system-ui;max-width:800px">' + ''.join(sections) + '</div>')
    dispute_info_panel.short_description = 'Информация о споре'

    # ─── Сортировка: споры первыми ────────────────────────────────────────────

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        from django.db.models import Case, When, Value, IntegerField
        return qs.annotate(
            _priority=Case(
                When(status='dispute', dispute_worker_defense__isnull=False, dispute_winner='', then=Value(1)),
                When(status='dispute', then=Value(2)),
                When(dispute_winner__isnull=False, then=Value(3)),
                default=Value(4),
                output_field=IntegerField()
            )
        ).order_by('_priority', '-created_at')

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    # ─── Арбитраж: групповые действия ────────────────────────────────────────

    @admin.action(description='✅ Разрешить спор в пользу КЛИЕНТА (возврат средств)')
    def resolve_dispute_client(self, request, queryset):
        auth_token = _get_admin_token()
        count, errors = 0, []

        for deal in queryset:
            if deal.status != 'dispute':
                errors.append(f'{str(deal.id)[:8]}: не в споре')
                continue
            if not deal.dispute_worker_defense:
                errors.append(f'{str(deal.id)[:8]}: исполнитель не ответил')
                continue
            if deal.dispute_winner:
                errors.append(f'{str(deal.id)[:8]}: уже разрешён')
                continue
            try:
                DealService.admin_resolve_dispute(
                    deal=deal, winner='client',
                    admin_comment=f'Решение администратора {request.user.email}: возврат клиенту',
                    auth_token=auth_token
                )
                count += 1
            except Exception as e:
                errors.append(f'{str(deal.id)[:8]}: {e}')

        if count:
            self.message_user(request, f'✅ Разрешено в пользу клиента: {count} спор(ов).', level=messages.SUCCESS)
        if errors:
            self.message_user(request, '⚠️ Пропущены: ' + ' | '.join(errors), level=messages.WARNING)

    @admin.action(description='✅ Разрешить спор в пользу ИСПОЛНИТЕЛЯ (выплата)')
    def resolve_dispute_worker(self, request, queryset):
        auth_token = _get_admin_token()
        count, errors = 0, []

        for deal in queryset:
            if deal.status != 'dispute':
                errors.append(f'{str(deal.id)[:8]}: не в споре')
                continue
            if not deal.dispute_worker_defense:
                errors.append(f'{str(deal.id)[:8]}: исполнитель не ответил')
                continue
            if deal.dispute_winner:
                errors.append(f'{str(deal.id)[:8]}: уже разрешён')
                continue
            try:
                DealService.admin_resolve_dispute(
                    deal=deal, winner='worker',
                    admin_comment=f'Решение администратора {request.user.email}: выплата исполнителю',
                    auth_token=auth_token
                )
                count += 1
            except Exception as e:
                errors.append(f'{str(deal.id)[:8]}: {e}')

        if count:
            self.message_user(request, f'✅ Разрешено в пользу исполнителя: {count} спор(ов).', level=messages.SUCCESS)
        if errors:
            self.message_user(request, '⚠️ Пропущены: ' + ' | '.join(errors), level=messages.WARNING)


# ─── Transaction ─────────────────────────────────────────────────────────────

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['id_short', 'deal_title', 'amount_formatted', 'status_badge', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['deal__title', 'deal__id']
    readonly_fields = ['id', 'deal', 'amount', 'commission', 'status',
                       'payment_provider', 'external_payment_id', 'created_at', 'updated_at']

    def id_short(self, obj):
        return str(obj.id)[:8] + '…'
    id_short.short_description = 'ID'

    def deal_title(self, obj):
        return obj.deal.title if obj.deal else '—'
    deal_title.short_description = 'Заказ'

    def amount_formatted(self, obj):
        return format_html('<b>{} ₽</b>', int(obj.amount))
    amount_formatted.short_description = 'Сумма'

    def status_badge(self, obj):
        colors = {
            'pending': '#6b7280', 'held': '#3b82f6',
            'captured': '#22c55e', 'refunded': '#f97316',
        }
        color = colors.get(obj.status, '#6b7280')
        return format_html(
            '<span style="background:{};color:#fff;padding:3px 8px;border-radius:8px;font-size:12px">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Статус'

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


# ─── Review ──────────────────────────────────────────────────────────────────

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['id_short', 'rating_stars', 'deal_title', 'created_at']
    list_filter = ['rating', 'created_at']
    search_fields = ['comment', 'deal__title']
    readonly_fields = ['id', 'deal', 'rating', 'comment', 'reviewer_id', 'reviewee_id', 'created_at']
    actions = ['delete_selected_reviews']

    def id_short(self, obj):
        return str(obj.id)[:8] + '…'
    id_short.short_description = 'ID'

    def deal_title(self, obj):
        return obj.deal.title if obj.deal else '—'
    deal_title.short_description = 'Заказ'

    def rating_stars(self, obj):
        stars = '★' * obj.rating + '☆' * (5 - obj.rating)
        color = '#f59e0b' if obj.rating >= 4 else ('#6b7280' if obj.rating >= 3 else '#ef4444')
        return format_html('<span style="color:{};font-size:16px">{}</span>', color, stars)
    rating_stars.short_description = 'Оценка'

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return True

    @admin.action(description='🗑️ Удалить выбранные отзывы')
    def delete_selected_reviews(self, request, queryset):
        count = queryset.count()
        queryset.delete()
        self.message_user(request, f'✅ Удалено {count} отзывов.', level=messages.SUCCESS)


# ─── Заголовки ────────────────────────────────────────────────────────────────

admin.site.site_header = 'MVS-Work — Маркетплейс'
admin.site.site_title = 'MVS Admin'
admin.site.index_title = 'Панель управления маркетплейсом'
