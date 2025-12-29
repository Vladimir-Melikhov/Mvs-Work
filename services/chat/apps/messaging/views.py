from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Room, Message
from .serializers import RoomSerializer, MessageSerializer
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync


class RoomViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def list(self, request):
        """Получить все комнаты пользователя"""
        user_id = str(request.user.id)
        rooms = Room.objects.filter(members__contains=[user_id]).order_by('-created_at')
        serializer = RoomSerializer(rooms, many=True)
        
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
            
            serializer = RoomSerializer(room)
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
        
        # Проверяем существующую комнату
        existing_room = Room.objects.filter(
            members__contains=[user1_id]
        ).filter(
            members__contains=[user2_id]
        ).first()
        
        if existing_room:
            serializer = RoomSerializer(existing_room)
            return Response({
                'status': 'success',
                'data': serializer.data,
                'message': 'Комната уже существует'
            })
        
        # Создаем новую
        room = Room.objects.create(members=[user1_id, user2_id])
        serializer = RoomSerializer(room)
        
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
            serializer = MessageSerializer(messages, many=True)
            
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
        Отправить интерактивное сообщение о сделке в комнату.
        Вызывается из Market Service через DealService.
        """
        try:
            room = Room.objects.get(id=pk)
            
            sender_id = request.data.get('sender_id')
            message_type = request.data.get('message_type', 'system')
            text = request.data.get('text', '')
            deal_data = request.data.get('deal_data', {})
            
            # Создаем сообщение
            message = Message.objects.create(
                room=room,
                sender_id=sender_id,
                text=text,
                message_type=message_type,
                deal_data=deal_data
            )
            
            # Отправляем через WebSocket всем участникам
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f'chat_{pk}',
                {
                    'type': 'chat_message',
                    'message': {
                        'id': str(message.id),
                        'room_id': str(message.room_id),
                        'sender_id': str(message.sender_id),
                        'text': message.text,
                        'message_type': message.message_type,
                        'deal_data': message.deal_data,
                        'created_at': message.created_at.isoformat(),
                    }
                }
            )
            
            return Response({
                'status': 'success',
                'data': MessageSerializer(message).data,
                'message': 'Сообщение отправлено'
            })
            
        except Room.DoesNotExist:
            return Response({'error': 'Комната не найдена'}, status=404)
        except Exception as e:
            return Response({'error': str(e)}, status=400)
