from rest_framework import serializers
from decimal import Decimal
from .models import Service, ServiceImage, Deal, Transaction, Review


class ServiceImageSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = ServiceImage
        fields = ['id', 'image', 'image_url', 'order', 'created_at']
        read_only_fields = ['id', 'created_at', 'image_url']
    
    def get_image_url(self, obj):
        """Формирует полный URL для изображения"""
        if not obj.image:
            return None
        
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(obj.image.url)
        return obj.image.url


class ServiceSerializer(serializers.ModelSerializer):
    owner_avatar = serializers.SerializerMethodField()
    images = ServiceImageSerializer(many=True, read_only=True)
    
    class Meta:
        model = Service
        fields = [
            'id', 'title', 'description', 'price', 
            'owner_id', 'owner_name', 'owner_avatar', 
            'ai_template', 'category', 'tags', 
            'created_at', 'updated_at', 'images',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'owner_id', 'images']
    
    def get_owner_avatar(self, obj):
        if not obj.owner_avatar:
            return None
        
        if obj.owner_avatar.startswith('http://') or obj.owner_avatar.startswith('https://'):
            return obj.owner_avatar
        
        request = self.context.get('request')
        if request:
            avatar_path = obj.owner_avatar.lstrip('/media/')
            return request.build_absolute_uri(f'/media/{avatar_path}')
        
        return obj.owner_avatar


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
    
    can_open_dispute = serializers.ReadOnlyField()
    can_worker_refund = serializers.ReadOnlyField()
    can_worker_defend = serializers.ReadOnlyField()
    is_dispute_pending_admin = serializers.ReadOnlyField()
    
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
        status_map = {
            'pending': 'Ожидает оплаты',
            'paid': 'В работе',
            'delivered': 'На проверке',
            'dispute': 'В споре',
            'completed': 'Завершён',
            'cancelled': 'Отменён',
        }
        
        base_status = status_map.get(obj.status, obj.status)
        
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
        if not obj.dispute_winner:
            return None
        
        return {
            'winner': obj.dispute_winner,
            'winner_text': 'клиента' if obj.dispute_winner == 'client' else 'исполнителя',
            'resolved_at': obj.dispute_resolved_at,
            'message': f"Спор разрешен в пользу {'клиента' if obj.dispute_winner == 'client' else 'исполнителя'}"
        }


class CreateDealSerializer(serializers.Serializer):
    chat_room_id = serializers.UUIDField()
    title = serializers.CharField(max_length=255)
    description = serializers.CharField()
    price = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=0)


class CompleteDealSerializer(serializers.Serializer):
    rating = serializers.IntegerField(min_value=1, max_value=5)
    comment = serializers.CharField(required=False, allow_blank=True)


class GenerateTZSerializer(serializers.Serializer):
    service_id = serializers.UUIDField()
    raw_requirements = serializers.CharField()
