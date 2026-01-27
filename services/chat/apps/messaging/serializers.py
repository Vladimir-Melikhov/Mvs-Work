from rest_framework import serializers
from .models import Room, Message, MessageAttachment


class MessageAttachmentSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()
    
    class Meta:
        model = MessageAttachment
        fields = ['id', 'filename', 'file_size', 'content_type', 'url', 'display_mode', 'created_at']
        read_only_fields = ['id', 'created_at', 'url']
    
    def get_url(self, obj):
        """Формирует полный URL для файла (либо локальный, либо external)"""
        file_url = obj.get_file_url()
        if not file_url:
            return None
        
        if not file_url.startswith('http'):
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(file_url)
        
        return file_url


class MessageSerializer(serializers.ModelSerializer):
    attachments = MessageAttachmentSerializer(many=True, read_only=True)
    
    class Meta:
        model = Message
        fields = ['id', 'sender_id', 'text', 'message_type', 'deal_data', 'attachments', 'created_at']
        read_only_fields = ['id', 'created_at', 'attachments']


class RoomSerializer(serializers.ModelSerializer):
    last_message = serializers.SerializerMethodField()

    class Meta:
        model = Room
        fields = ['id', 'members', 'last_message', 'created_at', 'deal_id']
        read_only_fields = ['id', 'created_at']

    def get_last_message(self, obj):
        last_msg = obj.messages.last()
        if last_msg:
            return MessageSerializer(last_msg, context=self.context).data
        return None


class CreateRoomSerializer(serializers.Serializer):
    member_ids = serializers.ListField(
        child=serializers.UUIDField(),
        min_length=2
    )
