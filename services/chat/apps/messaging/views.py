from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from .models import Room, Message, MessageAttachment
from .serializers import RoomSerializer, MessageSerializer, MessageAttachmentSerializer
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.core.files.base import ContentFile
import os
import uuid


class RoomViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def list(self, request):
        """Получить все комнаты пользователя"""
        user_id = str(request.user.id)
        rooms = Room.objects.filter(members__contains=[user_id]).order_by('-created_at')
        serializer = RoomSerializer(rooms, many=True, context={'request': request})
        
        return Response({
            'status': 'success',
            'data': serializer.data,
            'error': None
        })

    def retrieve(self, request, pk=None):
        """Получить конкретную комнату"""
        try:
            room = Room.objects.get(id=pk)
            user_id = str(request.user.id)
            
            if user_id not in room.members:
                return Response({'error': 'Нет доступа'}, status=403)
            
            serializer = RoomSerializer(room, context={'request': request})
            return Response({
                'status': 'success',
                'data': serializer.data,
                'error': None
            })
        except Room.DoesNotExist:
            return Response({'error': 'Комната не найдена'}, status=404)

    @action(detail=False, methods=['post'], url_path='create_room')
    def create_room(self, request):
        """Создать комнату между двумя пользователями"""
        user1_id = str(request.user.id)
        user2_id = request.data.get('user2_id')

        if not user2_id:
            return Response({'error': 'user2_id обязателен'}, status=400)

        existing_room = Room.objects.filter(
            members__contains=[user1_id]
        ).filter(
            members__contains=[user2_id]
        ).first()

        if existing_room:
            serializer = RoomSerializer(existing_room, context={'request': request})
            return Response({
                'status': 'success',
                'data': serializer.data,
                'message': 'Комната уже существует'
            })

        room = Room.objects.create(members=[user1_id, user2_id])
        serializer = RoomSerializer(room, context={'request': request})

        return Response({
            'status': 'success',
            'data': serializer.data,
            'message': 'Комната создана'
        }, status=201)

    @action(detail=True, methods=['get'])
    def messages(self, request, pk=None):
        """Получить историю сообщений комнаты"""
        try:
            room = Room.objects.get(id=pk)
            user_id = str(request.user.id)
            
            if user_id not in room.members:
                return Response({'error': 'Нет доступа'}, status=403)
            
            messages = room.messages.all().order_by('created_at')
            serializer = MessageSerializer(messages, many=True, context={'request': request})
            
            return Response({
                'status': 'success',
                'data': serializer.data,
                'error': None
            })
        except Room.DoesNotExist:
            return Response({'error': 'Комната не найдена'}, status=404)

    @action(detail=True, methods=['post'])
    def send_deal_message(self, request, pk=None):
        """
        Отправить или обновить интерактивное сообщение о сделке в комнату
        """
        try:
            room = Room.objects.get(id=pk)
            
            sender_id = request.data.get('sender_id')
            message_type = request.data.get('message_type', 'system')
            text = request.data.get('text', '')
            deal_data = request.data.get('deal_data', {})
            update_message_id = request.data.get('update_message_id')
            attachments_data = request.data.get('attachments', [])
            
            if update_message_id:
                try:
                    message = Message.objects.get(id=update_message_id, room=room)
                    
                    message.text = text
                    message.message_type = message_type
                    message.deal_data = deal_data
                    message.save()
                    
                    channel_layer = get_channel_layer()
                    async_to_sync(channel_layer.group_send)(
                        f'chat_{pk}',
                        {
                            'type': 'message_updated',
                            'message': self._serialize_message(message, request)
                        }
                    )
                    
                    return Response({
                        'status': 'success',
                        'data': MessageSerializer(message, context={'request': request}).data,
                        'message': 'Сообщение обновлено'
                    })
                    
                except Message.DoesNotExist:
                    pass
            
            message = Message.objects.create(
                room=room,
                sender_id=sender_id,
                text=text,
                message_type=message_type,
                deal_data=deal_data
            )
            
            if attachments_data:
                for att_data in attachments_data:
                    MessageAttachment.objects.create(
                        message=message,
                        filename=att_data.get('filename', 'file'),
                        file_size=att_data.get('file_size', 0),
                        content_type=att_data.get('content_type', 'application/octet-stream'),
                        external_url=att_data.get('url', '')
                    )
            
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f'chat_{pk}',
                {
                    'type': 'chat_message',
                    'message': self._serialize_message(message, request)
                }
            )
            
            return Response({
                'status': 'success',
                'data': MessageSerializer(message, context={'request': request}).data,
                'message': 'Сообщение отправлено'
            })
            
        except Room.DoesNotExist:
            return Response({'error': 'Комната не найдена'}, status=404)
        except Exception as e:
            return Response({'error': str(e)}, status=400)

    @action(detail=False, methods=['post'], url_path='upload')
    def upload_files(self, request):
        """
        ✅ КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ: Загрузка файлов БЕЗ ОБРАБОТКИ Pillow
        Использует ContentFile для сохранения файлов "как есть"
        """
        try:
            files = request.FILES.getlist('files')
            if not files:
                return Response({'error': 'Файлы не найдены в запросе'}, status=400)

            uploaded_files = []
            for file in files:
                # Валидация размера
                if file.size > 20 * 1024 * 1024:
                    return Response({'error': f'Файл {file.name} > 20MB'}, status=400)

                print(f"📥 Получен файл: {file.name}, размер: {file.size} байт")

                # ✅ КРИТИЧЕСКИ ВАЖНО: Читаем файл как байты БЕЗ обработки Pillow
                file_content = file.read()
                
                print(f"✅ Прочитано {len(file_content)} байт из файла")
                
                # Создаем ContentFile из байтов - это обходит обработку Django/Pillow
                content_file = ContentFile(file_content)
                
                # Генерируем уникальное имя файла
                ext = os.path.splitext(file.name)[1]
                unique_filename = f"{uuid.uuid4()}{ext}"
                
                # Создаем вложение с временным file_size
                attachment = MessageAttachment.objects.create(
                    message=None,
                    filename=file.name,
                    file_size=0,  # ✅ Временное значение, обновим после сохранения
                    content_type=file.content_type or 'application/octet-stream'
                )
                
                # Сохраняем файл вручную через ContentFile (без обработки)
                attachment.file.save(unique_filename, content_file, save=False)
                
                # ✅ КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ: Используем РЕАЛЬНЫЙ размер ПОСЛЕ сохранения
                attachment.file_size = attachment.file.size
                attachment.save()
                
                # Проверяем что размер сохранился правильно
                print(f"💾 Сохранено: {attachment.file.name}, размер: {attachment.file_size} байт")
                
                if attachment.file_size != len(file_content):
                    print(f"⚠️ ВНИМАНИЕ: Размер изменился! Было: {len(file_content)}, стало: {attachment.file_size}")

                # Формируем полный URL
                file_url = request.build_absolute_uri(attachment.file.url)

                uploaded_files.append({
                    'id': str(attachment.id),
                    'name': attachment.filename,
                    'size': attachment.file_size,
                    'url': file_url
                })

            return Response({'status': 'success', 'data': {'files': uploaded_files}})
        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response({'error': str(e)}, status=400)

    def _serialize_message(self, message, request):
        """Сериализация сообщения для WebSocket"""
        attachments = []
        for att in message.attachments.all():
            file_url = att.get_file_url()
            if not file_url:
                continue
                
            if not file_url.startswith('http'):
                file_url = request.build_absolute_uri(file_url)
                
            attachments.append({
                'id': str(att.id),
                'name': att.filename,
                'filename': att.filename,
                'size': att.file_size,
                'file_size': att.file_size,
                'content_type': att.content_type,
                'url': file_url
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
