from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from .models import Room, Message, MessageAttachment, ReadReceipt
from .serializers import RoomSerializer, MessageSerializer, MessageAttachmentSerializer
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.core.files.uploadedfile import UploadedFile
from django.core.files.base import File
from django.db.models import Max, Q
import os
import uuid
import magic


class RoomViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def _validate_file(self, file, max_size_mb=20):
        """Валидация файла с MIME-type проверкой"""
        if file.size > max_size_mb * 1024 * 1024:
            raise ValueError(f'Файл превышает {max_size_mb}MB')
        
        # MIME-type проверка
        file_head = file.read(2048)
        file.seek(0)
        
        mime = magic.from_buffer(file_head, mime=True)
        
        # Разрешенные MIME-types (расширенный список)
        allowed_mimes = [
            # Изображения
            'image/jpeg', 'image/png', 'image/gif', 'image/webp', 'image/svg+xml',
            # Документы
            'application/pdf',
            'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'application/vnd.ms-excel',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'application/vnd.ms-powerpoint',
            'application/vnd.openxmlformats-officedocument.presentationml.presentation',
            # Текстовые
            'text/plain', 'text/csv', 'text/html',
            # Архивы
            'application/zip', 'application/x-rar-compressed', 'application/x-7z-compressed',
            # Видео
            'video/mp4', 'video/mpeg', 'video/quicktime', 'video/x-msvideo',
            # Аудио
            'audio/mpeg', 'audio/wav', 'audio/ogg',
            # Код
            'application/json', 'application/xml',
            # Общий бинарный (для неопределенных типов)
            'application/octet-stream'
        ]
        
        # Для application/octet-stream проверяем расширение
        if mime == 'application/octet-stream':
            ext = os.path.splitext(file.name)[1].lower()
            safe_extensions = [
                '.txt', '.pdf', '.doc', '.docx', '.xls', '.xlsx', 
                '.ppt', '.pptx', '.zip', '.rar', '.7z', '.json', 
                '.xml', '.csv', '.jpg', '.jpeg', '.png', '.gif'
            ]
            if ext not in safe_extensions:
                raise ValueError(f'Небезопасный тип файла: {mime} с расширением {ext}')
        elif mime not in allowed_mimes:
            raise ValueError(f'Недопустимый MIME-type: {mime}')
        
        return True

    def list(self, request):
        """Получить все комнаты пользователя с правильной сортировкой"""
        user_id = str(request.user.id)
        rooms = Room.objects.filter(
            members__contains=[user_id]
        ).order_by('-updated_at')  # Сортировка по времени последнего сообщения
        
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

    @action(detail=True, methods=['post'], url_path='mark-read')
    def mark_read(self, request, pk=None):
        """Отметить все сообщения как прочитанные"""
        try:
            room = Room.objects.get(id=pk)
            user_id = str(request.user.id)
            
            if user_id not in room.members:
                return Response({'error': 'Нет доступа'}, status=403)
            
            # Получаем последнее сообщение в комнате
            last_message = room.messages.last()
            
            if last_message:
                # Обновляем или создаем запись о прочтении
                ReadReceipt.objects.update_or_create(
                    room=room,
                    user_id=user_id,
                    defaults={
                        'last_read_message': last_message
                    }
                )
            
            return Response({
                'status': 'success',
                'message': 'Сообщения отмечены как прочитанные'
            })
            
        except Room.DoesNotExist:
            return Response({'error': 'Комната не найдена'}, status=404)

    @action(detail=True, methods=['post'])
    def send_deal_message(self, request, pk=None):
        """Отправить или обновить интерактивное сообщение о сделке в комнату"""
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
                        external_url=att_data.get('url', ''),
                        display_mode='attachment'
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
        """Для изображений со сжатием (display_mode = 'inline')"""
        try:
            files = request.FILES.getlist('files')
            if not files:
                return Response({'error': 'Файлы не найдены в запросе'}, status=400)

            uploaded_files = []
            for file in files:
                try:
                    self._validate_file(file, max_size_mb=20)
                    
                    attachment = MessageAttachment(
                        message=None,
                        filename=file.name,
                        file_size=file.size,
                        content_type=file.content_type or 'application/octet-stream',
                        display_mode='inline'
                    )
                    
                    ext = os.path.splitext(file.name)[1]
                    unique_filename = f"{uuid.uuid4()}{ext}"
                    
                    attachment.file.save(unique_filename, file, save=True)
                    
                    actual_size = attachment.file.size
                    if actual_size != file.size:
                        attachment.file_size = actual_size
                        attachment.save(update_fields=['file_size'])

                    file_url = request.build_absolute_uri(attachment.file.url)

                    uploaded_files.append({
                        'id': str(attachment.id),
                        'name': attachment.filename,
                        'size': attachment.file_size,
                        'url': file_url
                    })
                    
                except ValueError as e:
                    print(f"Ошибка валидации файла {file.name}: {e}")
                    continue

            return Response({'status': 'success', 'data': {'files': uploaded_files}})
        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response({'error': str(e)}, status=400)

    @action(detail=False, methods=['post'], url_path='upload-raw-files')
    def upload_raw_files(self, request):
        """Для СЫРЫХ файлов БЕЗ обработки (display_mode = 'attachment')"""
        try:
            files = request.FILES.getlist('files')
            
            if not files:
                return Response({
                    'status': 'error',
                    'error': 'Файлы не переданы'
                }, status=400)
            
            uploaded = []
            
            for uploaded_file in files:
                try:
                    self._validate_file(uploaded_file, max_size_mb=20)
                    
                    original_size = uploaded_file.size
                    original_name = uploaded_file.name
                    
                    attachment = MessageAttachment(
                        message=None,
                        filename=original_name,
                        file_size=original_size,
                        content_type=uploaded_file.content_type or 'application/octet-stream',
                        display_mode='attachment'
                    )
                    
                    ext = os.path.splitext(original_name)[1]
                    unique_filename = f"{uuid.uuid4()}{ext}"
                    
                    attachment.file.save(
                        unique_filename, 
                        File(uploaded_file),
                        save=True
                    )
                    
                    actual_size = attachment.file.size
                    if actual_size != original_size:
                        attachment.file_size = actual_size
                        attachment.save(update_fields=['file_size'])
                    
                    file_url = request.build_absolute_uri(attachment.file.url)
                    
                    uploaded.append({
                        'id': str(attachment.id),
                        'name': attachment.filename,
                        'size': attachment.file_size,
                        'url': file_url,
                        'content_type': attachment.content_type
                    })
                    
                except ValueError as e:
                    print(f"Ошибка валидации файла {uploaded_file.name}: {e}")
                    continue
            
            return Response({
                'status': 'success',
                'data': {'files': uploaded}
            })
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response({
                'status': 'error',
                'error': str(e)
            }, status=400)

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
