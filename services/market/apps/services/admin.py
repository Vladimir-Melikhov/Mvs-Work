import uuid
import os
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import Service, Deal, Transaction, Review
from .deal_service import DealService
import requests


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
        'dispute_status',
        'created_at'
    ]
    list_filter = ['status', 'created_at', 'dispute_winner']
    search_fields = ['title', 'client_id', 'worker_id', 'id']
    
    # ВСЕ ПОЛЯ ТОЛЬКО ДЛЯ ЧТЕНИЯ - нельзя менять вручную
    readonly_fields = [
        'id',
        'chat_room_id',
        'client_id', 
        'worker_id',
        'service',
        'title',
        'description',
        'price',
        'status',
        'revision_count',
        'max_revisions',
        'delivery_message',
        'completion_message',
        'cancellation_reason',
        'dispute_info',
        'dispute_client_reason',
        'dispute_worker_defense',
        'dispute_created_at',
        'dispute_resolved_at',
        'dispute_winner',
        'created_at', 
        'paid_at', 
        'delivered_at', 
        'completed_at', 
        'cancelled_at',
    ]
    
    fieldsets = (
        ('🔥 АРБИТРАЖ - ИНФОРМАЦИЯ О СПОРЕ', {
            'fields': ('dispute_info',),
            'classes': ('wide',),
            'description': 'Используйте действия "Разрешить спор в пользу..." для принятия решения'
        }),
        ('Основная информация', {
            'fields': ('id', 'title', 'price', 'status'),
            'classes': ('collapse',)
        }),
        ('Участники', {
            'fields': ('client_id', 'worker_id'),
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
    
    def dispute_status(self, obj):
        """Показывает статус спора и победителя"""
        if obj.status != 'dispute' and not obj.dispute_winner:
            return '-'
        
        # Спор разрешен
        if obj.dispute_winner:
            if obj.dispute_winner == 'client':
                return format_html(
                    '<span style="background-color: #22c55e; color: white; padding: 5px 10px; border-radius: 5px; font-weight: bold;">✅ Клиент победил</span>'
                )
            else:
                return format_html(
                    '<span style="background-color: #3b82f6; color: white; padding: 5px 10px; border-radius: 5px; font-weight: bold;">✅ Исполнитель победил</span>'
                )
        
        # Спор активен
        if not obj.dispute_worker_defense:
            return format_html(
                '<span style="background-color: #f97316; color: white; padding: 5px 8px; border-radius: 5px;">⏳ Ждет исполнителя</span>'
            )
        
        return format_html(
            '<span style="background-color: #ef4444; color: white; padding: 5px 8px; border-radius: 5px; font-weight: bold; animation: pulse 2s infinite;">⚡ ТРЕБУЕТ РЕШЕНИЯ</span>'
        )
    dispute_status.short_description = 'Спор'
    
    def dispute_info(self, obj):
        """Показывает всю информацию о споре в удобном виде"""
        
        if obj.status != 'dispute' and not obj.dispute_winner:
            return format_html('<p style="color: #6b7280; font-size: 14px;">Заказ не в споре</p>')
        
        html = '<div style="font-family: system-ui; max-width: 900px;">'
        
        # Заголовок
        if obj.dispute_winner:
            winner_text = '👤 КЛИЕНТ ВЫИГРАЛ' if obj.dispute_winner == 'client' else '🛠️ ИСПОЛНИТЕЛЬ ВЫИГРАЛ'
            winner_color = '#22c55e' if obj.dispute_winner == 'client' else '#3b82f6'
            html += f'<div style="background: {winner_color}; color: white; padding: 15px; border-radius: 8px; margin-bottom: 20px; font-size: 18px; font-weight: bold; text-align: center;">'
            html += f'✅ СПОР РАЗРЕШЕН: {winner_text}'
            html += f'<div style="font-size: 14px; margin-top: 5px; opacity: 0.9;">Дата: {obj.dispute_resolved_at.strftime("%d.%m.%Y %H:%M") if obj.dispute_resolved_at else "—"}</div>'
            html += '</div>'
        else:
            html += '<div style="background: #ef4444; color: white; padding: 15px; border-radius: 8px; margin-bottom: 20px; font-size: 18px; font-weight: bold; text-align: center;">'
            html += '⚡ АКТИВНЫЙ СПОР - ТРЕБУЕТ РЕШЕНИЯ'
            if not obj.dispute_worker_defense:
                html += '<div style="font-size: 14px; margin-top: 5px; opacity: 0.9;">⏳ Исполнитель еще не ответил</div>'
            html += '</div>'
        
        # Основная информация
        html += '<div style="background: #f3f4f6; padding: 15px; border-radius: 8px; margin-bottom: 15px;">'
        html += f'<div style="margin-bottom: 8px;"><strong>📋 Заказ:</strong> {obj.title}</div>'
        html += f'<div style="margin-bottom: 8px;"><strong>💰 Сумма:</strong> {obj.price}₽</div>'
        html += f'<div style="margin-bottom: 8px;"><strong>👤 Клиент ID:</strong> {str(obj.client_id)[:8]}...</div>'
        html += f'<div><strong>🛠️ Исполнитель ID:</strong> {str(obj.worker_id)[:8]}...</div>'
        html += '</div>'
        
        # Техническое задание
        html += '<div style="background: white; border: 2px solid #e5e7eb; padding: 15px; border-radius: 8px; margin-bottom: 15px;">'
        html += '<div style="font-weight: bold; color: #374151; margin-bottom: 10px; font-size: 15px;">📝 ТЕХНИЧЕСКОЕ ЗАДАНИЕ</div>'
        html += f'<div style="color: #4b5563; line-height: 1.6; white-space: pre-wrap;">{obj.description}</div>'
        html += '</div>'
        
        # Результат работы
        if obj.delivery_message:
            html += '<div style="background: white; border: 2px solid #10b981; padding: 15px; border-radius: 8px; margin-bottom: 15px;">'
            html += '<div style="font-weight: bold; color: #059669; margin-bottom: 10px; font-size: 15px;">📦 РЕЗУЛЬТАТ РАБОТЫ (от исполнителя)</div>'
            html += f'<div style="color: #4b5563; line-height: 1.6; white-space: pre-wrap;">{obj.delivery_message}</div>'
            html += '</div>'
        
        # Претензия клиента
        html += '<div style="background: #fee2e2; border: 2px solid #ef4444; padding: 15px; border-radius: 8px; margin-bottom: 15px;">'
        html += '<div style="font-weight: bold; color: #dc2626; margin-bottom: 10px; font-size: 15px;">👤 ПРЕТЕНЗИЯ КЛИЕНТА</div>'
        html += f'<div style="color: #991b1b; line-height: 1.6; white-space: pre-wrap; font-size: 14px;">{obj.dispute_client_reason}</div>'
        html += '</div>'
        
        # Защита исполнителя
        if obj.dispute_worker_defense:
            html += '<div style="background: #dbeafe; border: 2px solid #3b82f6; padding: 15px; border-radius: 8px; margin-bottom: 15px;">'
            html += '<div style="font-weight: bold; color: #2563eb; margin-bottom: 10px; font-size: 15px;">🛡️ ЗАЩИТА ИСПОЛНИТЕЛЯ</div>'
            html += f'<div style="color: #1e40af; line-height: 1.6; white-space: pre-wrap; font-size: 14px;">{obj.dispute_worker_defense}</div>'
            html += '</div>'
        else:
            html += '<div style="background: #fef3c7; border: 2px solid #f59e0b; padding: 15px; border-radius: 8px; margin-bottom: 15px; text-align: center;">'
            html += '<div style="color: #92400e; font-weight: bold;">⏳ Исполнитель еще не подал защиту</div>'
            html += '<div style="color: #78350f; font-size: 13px; margin-top: 5px;">Решение можно принять только после ответа исполнителя</div>'
            html += '</div>'
        
        # Инструкция
        if not obj.dispute_winner and obj.dispute_worker_defense:
            html += '<div style="background: #fef3c7; border: 2px solid #f59e0b; padding: 15px; border-radius: 8px; text-align: center;">'
            html += '<div style="color: #92400e; font-weight: bold; font-size: 16px; margin-bottom: 8px;">⚡ КАК РАЗРЕШИТЬ СПОР</div>'
            html += '<div style="color: #78350f; font-size: 14px;">1. Вернитесь к списку заказов</div>'
            html += '<div style="color: #78350f; font-size: 14px;">2. Выберите этот заказ галочкой</div>'
            html += '<div style="color: #78350f; font-size: 14px;">3. В выпадающем меню "Действие" выберите:</div>'
            html += '<div style="color: #78350f; font-size: 14px; margin-top: 5px;">   • "✅ Разрешить спор в пользу КЛИЕНТА" (возврат средств)</div>'
            html += '<div style="color: #78350f; font-size: 14px;">   • "✅ Разрешить спор в пользу ИСПОЛНИТЕЛЯ" (выплата)</div>'
            html += '<div style="color: #78350f; font-size: 14px; margin-top: 5px;">4. Нажмите "Выполнить"</div>'
            html += '</div>'
        
        html += '</div>'
        
        return mark_safe(html)
    dispute_info.short_description = 'Информация о споре'
    
    def get_queryset(self, request):
        """Споры с защитой первыми, потом остальные споры, потом все остальное"""
        qs = super().get_queryset(request)
        from django.db.models import Case, When, Value, IntegerField
        
        return qs.annotate(
            dispute_priority=Case(
                # Споры требующие решения - самый высокий приоритет
                When(status='dispute', dispute_worker_defense__isnull=False, dispute_winner='', then=Value(1)),
                # Споры ожидающие ответа исполнителя
                When(status='dispute', dispute_worker_defense='', then=Value(2)),
                # Разрешенные споры
                When(dispute_winner__isnull=False, then=Value(3)),
                # Все остальное
                default=Value(4),
                output_field=IntegerField()
            )
        ).order_by('dispute_priority', '-created_at')
    
    def has_add_permission(self, request):
        """Запрещаем создавать заказы через админку"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Запрещаем удалять заказы"""
        return False
    
    def _get_admin_token(self):
        """
        ✅ КЛЮЧЕВОЕ ИСПРАВЛЕНИЕ: Получаем системный токен для обновления чата
        Этот токен используется для отправки обновлений в чат от имени системы
        """
        # ✅ Поддержка входа как по email, так и по username
        admin_username = os.getenv('ADMIN_USERNAME')  # Для входа по username
        admin_email = os.getenv('ADMIN_EMAIL')        # Для входа по email
        admin_password = os.getenv('ADMIN_PASSWORD', 'admin123')
        auth_service_url = os.getenv('AUTH_SERVICE_URL', 'http://localhost:8001')
        
        try:
            login_field = 'username' if admin_username else 'email'
            login_value = admin_username if admin_username else admin_email
            
            response = requests.post(
                f"{auth_service_url}/api/auth/login/",
                json={login_field: login_value, 'password': admin_password},
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get('data', {}).get('tokens', {}).get('access', '')
            else:
                print(f"⚠️ Не удалось получить токен администратора: {response.status_code}")
                return ''
        except Exception as e:
            print(f"🔥 Ошибка получения токена: {e}")
            return ''
    
    @admin.action(description='✅ Разрешить спор в пользу КЛИЕНТА (возврат средств)')
    def resolve_dispute_client(self, request, queryset):
        """Разрешить споры в пользу клиента - возврат средств"""
        count = 0
        errors = []
        
        # ✅ Получаем системный токен для обновления чата
        admin_token = self._get_admin_token()
        
        for deal in queryset:
            # Проверки
            if deal.status != 'dispute':
                errors.append(f"Заказ {str(deal.id)[:8]}: не в споре (статус: {deal.get_status_display()})")
                continue
            
            if not deal.dispute_worker_defense:
                errors.append(f"Заказ {str(deal.id)[:8]}: исполнитель еще не ответил")
                continue
            
            if deal.dispute_winner:
                errors.append(f"Заказ {str(deal.id)[:8]}: спор уже разрешен")
                continue
            
            try:
                DealService.admin_resolve_dispute(
                    deal=deal,
                    winner='client',
                    admin_comment=f'Решение администратора {request.user.username}: средства возвращены клиенту',
                    auth_token=admin_token  # ✅ Передаем токен
                )
                count += 1
            except Exception as e:
                errors.append(f"Заказ {str(deal.id)[:8]}: {str(e)}")
        
        # Сообщения
        if count:
            self.message_user(
                request, 
                f'✅ Разрешено {count} спор(ов) в пользу КЛИЕНТА. Средства возвращены клиенту, заказы отменены.',
                level='success'
            )
        
        if errors:
            self.message_user(
                request, 
                '⚠️ Некоторые заказы не обработаны: ' + ' | '.join(errors), 
                level='warning'
            )
        
        if not count and not errors:
            self.message_user(request, '❌ Не выбрано ни одного подходящего заказа', level='error')
    
    @admin.action(description='✅ Разрешить спор в пользу ИСПОЛНИТЕЛЯ (выплата)')
    def resolve_dispute_worker(self, request, queryset):
        """Разрешить споры в пользу исполнителя - выплата средств"""
        count = 0
        errors = []
        
        # ✅ Получаем системный токен для обновления чата
        admin_token = self._get_admin_token()
        
        for deal in queryset:
            # Проверки
            if deal.status != 'dispute':
                errors.append(f"Заказ {str(deal.id)[:8]}: не в споре (статус: {deal.get_status_display()})")
                continue
            
            if not deal.dispute_worker_defense:
                errors.append(f"Заказ {str(deal.id)[:8]}: исполнитель еще не ответил")
                continue
            
            if deal.dispute_winner:
                errors.append(f"Заказ {str(deal.id)[:8]}: спор уже разрешен")
                continue
            
            try:
                DealService.admin_resolve_dispute(
                    deal=deal,
                    winner='worker',
                    admin_comment=f'Решение администратора {request.user.username}: работа принята, средства выплачены исполнителю',
                    auth_token=admin_token  # ✅ Передаем токен
                )
                count += 1
            except Exception as e:
                errors.append(f"Заказ {str(deal.id)[:8]}: {str(e)}")
        
        # Сообщения
        if count:
            self.message_user(
                request, 
                f'✅ Разрешено {count} спор(ов) в пользу ИСПОЛНИТЕЛЯ. Средства выплачены исполнителю, заказы завершены.',
                level='success'
            )
        
        if errors:
            self.message_user(
                request, 
                '⚠️ Некоторые заказы не обработаны: ' + ' | '.join(errors), 
                level='warning'
            )
        
        if not count and not errors:
            self.message_user(request, '❌ Не выбрано ни одного подходящего заказа', level='error')


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['id_short', 'deal_title', 'amount', 'status_badge', 'created_at']
    list_filter = ['status', 'created_at']
    readonly_fields = ['id', 'deal', 'amount', 'commission', 'status', 'payment_provider', 'external_payment_id', 'created_at', 'updated_at']
    
    def id_short(self, obj):
        return str(obj.id)[:8]
    id_short.short_description = 'ID'
    
    def deal_title(self, obj):
        return obj.deal.title if obj.deal else '-'
    deal_title.short_description = 'Заказ'
    
    def status_badge(self, obj):
        colors = {
            'pending': '#6b7280',
            'held': '#3b82f6',
            'captured': '#22c55e',
            'refunded': '#f97316',
        }
        color = colors.get(obj.status, '#6b7280')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 5px 10px; border-radius: 5px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Статус'
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['id_short', 'rating', 'deal_title', 'created_at']
    list_filter = ['rating', 'created_at']
    readonly_fields = ['id', 'deal', 'rating', 'comment', 'reviewer_id', 'reviewee_id', 'created_at']
    
    def id_short(self, obj):
        return str(obj.id)[:8]
    id_short.short_description = 'ID'
    
    def deal_title(self, obj):
        return obj.deal.title if obj.deal else '-'
    deal_title.short_description = 'Заказ'
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False


admin.site.site_header = 'Маркетплейс - Админ-панель'
admin.site.site_title = 'Админка'
admin.site.index_title = 'Управление маркетплейсом'