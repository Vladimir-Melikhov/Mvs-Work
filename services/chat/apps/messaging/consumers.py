# services/chat/apps/messaging/consumers.py
import json
import uuid
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Room, Message, MessageAttachment
from .notification_service import TelegramNotificationService


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # 1. Проверка аутентификации
        user = self.scope.get('user')
        if not user or not user.is_authenticated:
            await self.close(code=4001)
            return
        
        # 2. Проверка членства в чате
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        is_member = await self.check_room_membership(str(user.id), self.room_id)
        
        if not is_member:
            await self.close(code=4003)  # Forbidden
            return
        
        self.room_group_name = f'chat_{self.room_id}'
        self.user_id = str(user.id)
        
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )

    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data.get('type', 'message')

        if message_type == 'message':
            # Валидация: отправитель должен быть текущим пользователем
            sender_id = data.get('sender_id')
            if str(sender_id) != self.user_id:
                return  # Игнорируем попытку отправить от чужого имени
            
            text = data.get('text', '')
            attachments = data.get('attachments', [])

            message = await self.save_message(
                room_id=self.room_id,
                sender_id=self.user_id,
                text=text,
                message_type='text',
                attachment_ids=attachments
            )

            # Отправка Telegram уведомления
            await self.send_telegram_notification(message, self.user_id)

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
    def check_room_membership(self, user_id, room_id):
        """Проверить, что пользователь - участник чата"""
        try:
            room = Room.objects.get(id=room_id)
            return str(user_id) in [str(m) for m in room.members]
        except Room.DoesNotExist:
            return False

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
    
    @database_sync_to_async
    def get_room_members(self, message):
        """Получить членов комнаты"""
        return message.room.members
    
    async def send_telegram_notification(self, message, sender_id):
        """
        Отправка Telegram уведомления через централизованный сервис
        """
        try:
            print(f"[TELEGRAM] 🔔 Отправка уведомления о сообщении {message.id}")
            
            # Получаем участников комнаты
            members = await self.get_room_members(message)
            
            # Используем сервис уведомлений
            notification_service = TelegramNotificationService()
            
            # Отправляем синхронно (т.к. внутри уже requests)
            success = await self.run_in_executor(
                notification_service.send_notification,
                message,
                sender_id,
                members
            )
            
            if success:
                print(f"[TELEGRAM] ✅ Уведомление успешно отправлено")
            else:
                print(f"[TELEGRAM] ⚠️ Уведомление не отправлено")
            
        except Exception as e:
            print(f"[TELEGRAM] ⚠️ Ошибка отправки уведомления: {e}")
            import traceback
            traceback.print_exc()
    
    @database_sync_to_async
    def run_in_executor(self, func, *args):
        """Запустить синхронную функцию в executor"""
        return func(*args)
