from rest_framework import serializers
from .models import Service, Order


class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = [
            'id', 'title', 'description', 'price', 'owner_id', 
            'owner_name', 'owner_avatar', 'ai_template',
            'tags', 'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'owner_id', 'owner_name', 'owner_avatar']


class OrderSerializer(serializers.ModelSerializer):
    service = ServiceSerializer(read_only=True)
    
    class Meta:
        model = Order
        fields = ['id', 'service', 'client_id', 'worker_id', 'status', 'agreed_tz', 'price', 'created_at']
        read_only_fields = ['id', 'created_at']


class GenerateTZSerializer(serializers.Serializer):
    service_id = serializers.UUIDField()
    raw_requirements = serializers.CharField()


class CreateOrderSerializer(serializers.Serializer):
    service_id = serializers.UUIDField()
    agreed_tz = serializers.CharField()