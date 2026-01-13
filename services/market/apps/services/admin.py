import uuid
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import Service, Deal, Transaction, Review
from .deal_service import DealService


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'price', 'owner_name', 'created_at']
    list_filter = ['category', 'created_at']
    search_fields = ['title', 'description', 'owner_name']
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('id', 'title', 'description', 'price', 'category')
        }),
        ('Владелец', {
            'fields': ('owner_id', 'owner_name', 'owner_avatar')
        }),
        ('Дополнительно', {
            'fields': ('ai_template', 'tags', 'created_at', 'updated_at')
        }),
    )


@admin.register(Deal)
class DealAdmin(admin.ModelAdmin):
    list_display = [
        'id_short', 
        'title', 
        'status_badge', 
        'price', 
        'client_worker',
        'dispute_badge',
        'created_at'
    ]
    list_filter = ['status', 'created_at']
    search_fields = ['title', 'client_id', 'worker_id', 'id']
    
    # КЛЮЧЕВОЕ ИСПРАВЛЕНИЕ: dispute_info добавлен в readonly_fields
    readonly_fields = [
        'id', 
        'dispute_info', 
        'created_at', 
        'paid_at', 
        'delivered_at', 
        'completed_at', 
        'cancelled_at',
        'dispute_created_at',
        'dispute_resolved_at'
    ]
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('id', 'chat_room_id', 'title', 'description', 'price', 'status')
        }),
        ('Участники', {
            'fields': ('client_id', 'worker_id', 'service')
        }),
        ('Доработки', {
            'fields': ('revision_count', 'max_revisions')
        }),
        ('Сообщения', {
            'fields': ('delivery_message', 'completion_message', 'cancellation_reason'),
            'classes': ('collapse',)
        }),
        ('🔥 АРБИТРАЖ', {
            'fields': (
                'dispute_info',
                'dispute_client_reason',
                'dispute_worker_defense',
                'dispute_created_at',
                'dispute_resolved_at',
                'dispute_winner'
            ),
            'classes': ('wide',)
        }),
        ('Временные метки', {
            'fields': ('created_at', 'paid_at', 'delivered_at', 'completed_at', 'cancelled_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['resolve_dispute_client', 'resolve_dispute_worker']
    
    def id_short(self, obj):
        return str(obj.id)[:8]
    id_short.short_description = 'ID'
    
    def status_badge(self, obj):
        colors = {
            'pending': '#9333ea',
            'paid': '#3b82f6',
            'delivered': '#22c55e',
            'dispute': '#ef4444',
            'completed': '#f97316',
            'cancelled': '#6b7280',
        }
        labels = {
            'pending': 'Ожидает',
            'paid': 'Оплачен',
            'delivered': 'Сдан',
            'dispute': '⚠️ СПОР',
            'completed': 'Завершён',
            'cancelled': 'Отменён',
        }
        color = colors.get(obj.status, '#6b7280')
        label = labels.get(obj.status, obj.status)
        return format_html(
            '<span style="background-color: {}; color: white; padding: 5px 10px; border-radius: 5px; font-weight: bold;">{}</span>',
            color, label
        )
    status_badge.short_description = 'Статус'
    
    def client_worker(self, obj):
        return format_html(
            '👤 Клиент: {}<br>🛠 Исполнитель: {}',
            str(obj.client_id)[:8], 
            str(obj.worker_id)[:8]
        )
    client_worker.short_description = 'Участники'
    
    def dispute_badge(self, obj):
        if obj.status != 'dispute':
            return '-'
        
        if not obj.dispute_worker_defense:
            return format_html(
                '<span style="background-color: #f97316; color: white; padding: 3px 8px; border-radius: 3px;">Ждет ответа исполнителя</span>'
            )
        
        if not obj.dispute_winner:
            return format_html(
                '<span style="background-color: #ef4444; color: white; padding: 3px 8px; border-radius: 3px; font-weight: bold;">⏳ ТРЕБУЕТ РЕШЕНИЯ</span>'
            )
        
        return format_html(
            '<span style="background-color: #22c55e; color: white; padding: 3px 8px; border-radius: 3px;">✓ Разрешен</span>'
        )
    dispute_badge.short_description = 'Спор'
    
    def dispute_info(self, obj):
        if obj.status != 'dispute':
            return format_html('<p style="color: #6b7280;">Заказ не в споре</p>')
        
        html = '<div style="background: #fee; padding: 15px; border-left: 4px solid #ef4444; margin: 10px 0;">'
        html += '<h3 style="margin-top: 0; color: #dc2626;">⚠️ АКТИВНЫЙ СПОР</h3>'
        
        # Претензия клиента
        html += '<div style="background: white; padding: 10px; margin: 10px 0; border-radius: 5px;">'
        html += '<strong style="color: #dc2626;">👤 Претензия клиента:</strong><br>'
        html += f'<pre style="white-space: pre-wrap; margin: 5px 0;">{obj.dispute_client_reason}</pre>'
        html += '</div>'
        
        # Защита исполнителя
        if obj.dispute_worker_defense:
            html += '<div style="background: white; padding: 10px; margin: 10px 0; border-radius: 5px;">'
            html += '<strong style="color: #2563eb;">🛡️ Защита исполнителя:</strong><br>'
            html += f'<pre style="white-space: pre-wrap; margin: 5px 0;">{obj.dispute_worker_defense}</pre>'
            html += '</div>'
        else:
            html += '<div style="background: #fef3c7; padding: 10px; margin: 10px 0; border-radius: 5px;">'
            html += '<strong style="color: #d97706;">⏳ Исполнитель еще не ответил</strong>'
            html += '</div>'
        
        # Результат работы
        if obj.delivery_message:
            html += '<div style="background: white; padding: 10px; margin: 10px 0; border-radius: 5px;">'
            html += '<strong style="color: #059669;">📦 Результат работы:</strong><br>'
            html += f'<pre style="white-space: pre-wrap; margin: 5px 0;">{obj.delivery_message}</pre>'
            html += '</div>'
        
        # Статус
        if obj.dispute_winner:
            winner_text = 'клиента' if obj.dispute_winner == 'client' else 'исполнителя'
            html += f'<div style="background: #d1fae5; padding: 10px; margin: 10px 0; border-radius: 5px; color: #065f46;">'
            html += f'<strong>✅ Спор разрешен в пользу {winner_text}</strong>'
            html += f'<br>Дата: {obj.dispute_resolved_at.strftime("%d.%m.%Y %H:%M") if obj.dispute_resolved_at else "—"}'
            html += '</div>'
        elif obj.dispute_worker_defense:
            html += '<div style="background: #fef3c7; padding: 10px; margin: 10px 0; border-radius: 5px; color: #92400e;">'
            html += '<strong>⚡ ТРЕБУЕТСЯ ВАШЕ РЕШЕНИЕ!</strong><br>'
            html += 'Используйте кнопки "Разрешить в пользу..." ниже или действия в списке заказов.'
            html += '</div>'
        
        html += '</div>'
        
        return mark_safe(html)
    dispute_info.short_description = 'Информация о споре'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.order_by('-status', '-created_at')
    
    @admin.action(description='✅ Разрешить спор в пользу КЛИЕНТА (возврат средств)')
    def resolve_dispute_client(self, request, queryset):
        count = 0
        errors = []
        for deal in queryset:
            if deal.status != 'dispute' or deal.dispute_winner:
                continue
            try:
                DealService.admin_resolve_dispute(
                    deal=deal,
                    winner='client',
                    admin_comment=f'Решение принято администратором {request.user.username}'
                )
                count += 1
            except Exception as e:
                errors.append(f"Заказ {deal.id}: {str(e)}")
        if count:
            self.message_user(request, f'✅ Разрешено {count} споров в пользу клиента.')
        if errors:
            self.message_user(request, '⚠️ Ошибки: ' + '; '.join(errors), level='warning')
    
    @admin.action(description='✅ Разрешить спор в пользу ИСПОЛНИТЕЛЯ (выплата)')
    def resolve_dispute_worker(self, request, queryset):
        count = 0
        errors = []
        for deal in queryset:
            if deal.status != 'dispute' or deal.dispute_winner:
                continue
            try:
                DealService.admin_resolve_dispute(
                    deal=deal,
                    winner='worker',
                    admin_comment=f'Решение принято администратором {request.user.username}'
                )
                count += 1
            except Exception as e:
                errors.append(f"Заказ {deal.id}: {str(e)}")
        if count:
            self.message_user(request, f'✅ Разрешено {count} споров в пользу исполнителя.')
        if errors:
            self.message_user(request, '⚠️ Ошибки: ' + '; '.join(errors), level='warning')


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['id_short', 'deal_title', 'amount', 'status_badge', 'created_at']
    readonly_fields = ['id', 'created_at', 'updated_at']
    def id_short(self, obj): return str(obj.id)[:8]
    def deal_title(self, obj): return obj.deal.title if obj.deal else '-'
    def status_badge(self, obj):
        return format_html('<span style="color: blue;">{}</span>', obj.get_status_display())

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['id_short', 'rating', 'created_at']
    readonly_fields = ['id', 'created_at']
    def id_short(self, obj): return str(obj.id)[:8]


admin.site.site_header = 'Маркетплейс - Админ-панель'
admin.site.index_title = 'Управление маркетплейсом'
