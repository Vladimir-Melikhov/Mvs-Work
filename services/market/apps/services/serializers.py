from rest_framework import serializers
from decimal import Decimal  # ✅ Добавлен обязательный импорт
from .models import Service, Deal, Transaction


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


class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = [
            'id', 'deal', 'amount', 'commission', 'status',
            'payment_provider', 'external_payment_id', 'payment_url',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class DealSerializer(serializers.ModelSerializer):
    service = ServiceSerializer(read_only=True)
    transactions = TransactionSerializer(many=True, read_only=True)
    
    # Дополнительные вычисляемые поля
    commission = serializers.SerializerMethodField()
    total = serializers.SerializerMethodField()
    
    class Meta:
        model = Deal
        fields = [
            'id', 'chat_room_id', 'client_id', 'worker_id',
            'service', 'title', 'description', 'price',
            'status', 'proposed_by', 'proposed_at',
            'client_confirmed', 'worker_confirmed',
            'history', 'created_at', 'updated_at',
            'activated_at', 'completed_at',
            'transactions', 'commission', 'total'
        ]
        read_only_fields = [
            'id', 'chat_room_id', 'created_at', 'updated_at',
            'activated_at', 'completed_at', 'proposed_by', 'proposed_at'
        ]
    
    def get_commission(self, obj):
        """Вычислить комиссию 8%"""
        # ✅ ИСПРАВЛЕНО: теперь умножаем Decimal на Decimal
        return float(obj.price * Decimal('0.08'))
    
    def get_total(self, obj):
        """Вычислить итоговую сумму с комиссией"""
        # ✅ ИСПРАВЛЕНО: теперь умножаем Decimal на Decimal
        return float(obj.price * Decimal('1.08'))


class ProposeDealSerializer(serializers.Serializer):
    """Для предложения/изменения условий сделки"""
    title = serializers.CharField(max_length=255)
    description = serializers.CharField()
    price = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=0)


class CancelDealSerializer(serializers.Serializer):
    """Для отмены сделки"""
    reason = serializers.CharField(required=False, default="Не указана")


class GenerateTZSerializer(serializers.Serializer):
    """Для AI-генерации ТЗ"""
    service_id = serializers.UUIDField()
    raw_requirements = serializers.CharField()
