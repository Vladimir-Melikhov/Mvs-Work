from rest_framework import serializers
from decimal import Decimal
from .models import Service, Deal, Transaction, Review


class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = [
            'id', 'title', 'description', 'price', 
            'owner_id', 'owner_name', 'owner_avatar', 
            'ai_template', 'category', 'tags', 
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'owner_id', 'owner_name', 'owner_avatar']


class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ['id', 'deal', 'rating', 'comment', 'reviewer_id', 'reviewee_id', 'created_at']
        read_only_fields = ['id', 'created_at']


class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = ['id', 'amount', 'commission', 'status', 'created_at']
        read_only_fields = ['id', 'created_at']


class DealSerializer(serializers.ModelSerializer):
    service = ServiceSerializer(read_only=True)
    transactions = TransactionSerializer(many=True, read_only=True)
    review = ReviewSerializer(read_only=True)
    
    commission = serializers.SerializerMethodField()
    total = serializers.SerializerMethodField()
    
    # ✅ Поля арбитража (read-only)
    can_open_dispute = serializers.ReadOnlyField()
    can_worker_refund = serializers.ReadOnlyField()
    can_worker_defend = serializers.ReadOnlyField()
    is_dispute_pending_admin = serializers.ReadOnlyField()
    
    # ✅ Читаемый статус с учетом спора
    status_display = serializers.SerializerMethodField()
    dispute_result = serializers.SerializerMethodField()

    class Meta:
        model = Deal
        fields = [
            'id', 'chat_room_id', 'client_id', 'worker_id',
            'service', 'title', 'description', 'price',
            'status', 'revision_count', 'max_revisions',
            'delivery_message', 'completion_message', 'cancellation_reason',
            'created_at', 'paid_at', 'delivered_at', 'completed_at', 'cancelled_at',
            'transactions', 'review', 'commission', 'total',
            'can_pay', 'can_deliver', 'can_request_revision', 'can_complete', 'can_cancel',
            # ✅ Новые поля арбитража
            'can_open_dispute', 'can_worker_refund', 'can_worker_defend', 'is_dispute_pending_admin',
            'dispute_client_reason', 'dispute_worker_defense', 
            'dispute_created_at', 'dispute_resolved_at', 'dispute_winner',
            'status_display', 'dispute_result',
        ]
        read_only_fields = ['id', 'chat_room_id', 'created_at']

    def get_commission(self, obj):
        return float(obj.price * Decimal('0.08'))

    def get_total(self, obj):
        return float(obj.price * Decimal('1.08'))
    
    def get_status_display(self, obj):
        """Возвращает читаемый статус с учетом результата спора"""
        status_map = {
            'pending': 'Ожидает оплаты',
            'paid': 'В работе',
            'delivered': 'На проверке',
            'dispute': 'В споре',
            'completed': 'Завершён',
            'cancelled': 'Отменён',
        }
        
        base_status = status_map.get(obj.status, obj.status)
        
        # Если есть победитель в споре - добавляем информацию
        if obj.dispute_winner:
            if obj.dispute_winner == 'client':
                if obj.status == 'cancelled':
                    return 'Отменён (спор - победа клиента)'
                return f'{base_status} (спор - победа клиента)'
            elif obj.dispute_winner == 'worker':
                if obj.status == 'completed':
                    return 'Завершён (спор - победа исполнителя)'
                return f'{base_status} (спор - победа исполнителя)'
        
        return base_status
    
    def get_dispute_result(self, obj):
        """Возвращает результат спора для отображения"""
        if not obj.dispute_winner:
            return None
        
        return {
            'winner': obj.dispute_winner,
            'winner_text': 'клиента' if obj.dispute_winner == 'client' else 'исполнителя',
            'resolved_at': obj.dispute_resolved_at,
            'message': f"Спор разрешен в пользу {'клиента' if obj.dispute_winner == 'client' else 'исполнителя'}"
        }


class CreateDealSerializer(serializers.Serializer):
    """Создание заказа"""
    chat_room_id = serializers.UUIDField()
    title = serializers.CharField(max_length=255)
    description = serializers.CharField()
    price = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=0)


class CompleteDealSerializer(serializers.Serializer):
    """Завершение заказа с отзывом"""
    rating = serializers.IntegerField(min_value=1, max_value=5)
    comment = serializers.CharField(required=False, allow_blank=True)


class GenerateTZSerializer(serializers.Serializer):
    """AI-генерация ТЗ"""
    service_id = serializers.UUIDField()
    raw_requirements = serializers.CharField()
