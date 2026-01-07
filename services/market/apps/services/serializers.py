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

    class Meta:
        model = Deal
        fields = [
            'id', 'chat_room_id', 'client_id', 'worker_id',
            'service', 'title', 'description', 'price',
            'status', 'revision_count', 'max_revisions',
            'delivery_message', 'completion_message', 'cancellation_reason',
            'created_at', 'paid_at', 'delivered_at', 'completed_at', 'cancelled_at',
            'transactions', 'review', 'commission', 'total',
            'can_pay', 'can_deliver', 'can_request_revision', 'can_complete', 'can_cancel'
        ]
        read_only_fields = ['id', 'chat_room_id', 'created_at']

    def get_commission(self, obj):
        return float(obj.price * Decimal('0.08'))

    def get_total(self, obj):
        return float(obj.price * Decimal('1.08'))


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
