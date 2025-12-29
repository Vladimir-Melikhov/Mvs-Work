from rest_framework import serializers
from .models import Room, Message


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ['id', 'sender_id', 'text', 'attachments', 'is_system', 'created_at']
        read_only_fields = ['id', 'created_at']


class RoomSerializer(serializers.ModelSerializer):
    last_message = serializers.SerializerMethodField()

    class Meta:
        model = Room
        fields = ['id', 'members', 'last_message', 'created_at']
        read_only_fields = ['id', 'created_at']

    def get_last_message(self, obj):
        last_msg = obj.messages.last()
        if last_msg:
            return MessageSerializer(last_msg).data
        return None


class CreateRoomSerializer(serializers.Serializer):
    member_ids = serializers.ListField(
        child=serializers.UUIDField(),
        min_length=2
    )
