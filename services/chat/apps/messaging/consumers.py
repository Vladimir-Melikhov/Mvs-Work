import json
import uuid
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Room, Message, MessageAttachment
from django.conf import settings


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f'chat_{self.room_id}'

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data.get('type', 'message')

        if message_type == 'message':
            sender_id = data.get('sender_id')
            text = data.get('text', '')
            attachments = data.get('attachments', [])

            message = await self.save_message(
                room_id=self.room_id,
                sender_id=sender_id,
                text=text,
                message_type='text',
                attachment_ids=attachments
            )

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': await self.serialize_message(message)
                }
            )

    async def chat_message(self, event):
        """Обработчик для отправки новых сообщений клиентам"""
        await self.send(text_data=json.dumps({
            'type': 'message',
            'data': event['message']
        }))
    
    async def message_updated(self, event):
        """Обработчик для обновления существующих сообщений"""
        await self.send(text_data=json.dumps({
            'type': 'message_updated',
            'data': event['message']
        }))

    @database_sync_to_async
    def save_message(self, room_id, sender_id, text, message_type='text', deal_data=None, attachment_ids=None):
        """Сохранить сообщение в БД и прикрепить файлы"""
        room = Room.objects.get(id=room_id)
        message = Message.objects.create(
            room=room,
            sender_id=sender_id,
            text=text,
            message_type=message_type,
            deal_data=deal_data
        )
        
        if attachment_ids:
            for att_id in attachment_ids:
                try:
                    attachment = MessageAttachment.objects.get(id=att_id, message__isnull=True)
                    attachment.message = message
                    attachment.save()
                except MessageAttachment.DoesNotExist:
                    pass
        
        return message

    @database_sync_to_async
    def serialize_message(self, message):
        """Сериализация сообщения для отправки"""
        attachments = []
        for att in message.attachments.all():
            file_url = att.get_file_url()
            if not file_url:
                continue
            
            if not file_url.startswith('http'):
                file_url = f"http://localhost:8003{file_url}"
            
            attachments.append({
                'id': str(att.id),
                'name': att.filename,
                'filename': att.filename,
                'size': att.file_size,
                'file_size': att.file_size,
                'content_type': att.content_type,
                'url': file_url,
                'display_mode': att.display_mode
            })
        
        return {
            'id': str(message.id),
            'room_id': str(message.room_id),
            'sender_id': str(message.sender_id),
            'text': message.text,
            'message_type': message.message_type,
            'deal_data': message.deal_data,
            'attachments': attachments,
            'created_at': message.created_at.isoformat(),
        }
