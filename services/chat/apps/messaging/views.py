from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.conf import settings
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import Room, Message
from .serializers import RoomSerializer, MessageSerializer, CreateRoomSerializer


class RoomViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def list(self, request):
        """Get all rooms for current user"""
        user_id = str(request.user.id)
        rooms = Room.objects.filter(members__contains=[user_id])
        serializer = RoomSerializer(rooms, many=True)
        
        return Response({
            'status': 'success',
            'data': serializer.data,
            'error': None
        }, status=status.HTTP_200_OK)

    def retrieve(self, request, pk=None):
        """Get room details"""
        try:
            room = Room.objects.get(id=pk)
            serializer = RoomSerializer(room)
            
            return Response({
                'status': 'success',
                'data': serializer.data,
                'error': None
            }, status=status.HTTP_200_OK)
            
        except Room.DoesNotExist:
            return Response({
                'status': 'error',
                'error': 'Room not found',
                'data': None
            }, status=status.HTTP_404_NOT_FOUND)

    def create(self, request):
        """Create new room"""
        serializer = CreateRoomSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response({
                'status': 'error',
                'error': serializer.errors,
                'data': None
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Преобразуем UUID объекты обратно в строки
        member_ids_str = [str(uid) for uid in serializer.validated_data['member_ids']]
        
        room = Room.objects.create(
            members=member_ids_str
        )
        
        return Response({
            'status': 'success',
            'data': RoomSerializer(room).data,
            'error': None
        }, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get'])
    def messages(self, request, pk=None):
        """Get messages for room"""
        try:
            room = Room.objects.get(id=pk)
            messages = room.messages.all()
            serializer = MessageSerializer(messages, many=True)
            
            return Response({
                'status': 'success',
                'data': serializer.data,
                'error': None
            }, status=status.HTTP_200_OK)
            
        except Room.DoesNotExist:
            return Response({
                'status': 'error',
                'error': 'Room not found',
                'data': None
            }, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['post'], url_path='send_message')
    def send_message(self, request, pk=None):
        """
        HTTP endpoint to send a message (used by other services)
        """
        try:
            room = Room.objects.get(id=pk)
            sender_id = request.data.get('sender_id')
            text = request.data.get('text')
            is_system = request.data.get('is_system', False)

            if not text or not sender_id:
                return Response({'error': 'text and sender_id are required'}, status=400)

            # 1. Сохраняем в БД
            message = Message.objects.create(
                room=room,
                sender_id=sender_id,
                text=text,
                is_system=is_system
            )

            # 2. Отправляем в WebSocket (чтобы обновилось в реальном времени)
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f'chat_{room.id}',
                {
                    'type': 'chat_message',
                    'message': {
                        'id': str(message.id),
                        'sender_id': str(message.sender_id),
                        'text': message.text,
                        'created_at': message.created_at.isoformat(),
                        'is_system': message.is_system
                    }
                }
            )

            return Response({
                'status': 'success',
                'data': MessageSerializer(message).data
            }, status=status.HTTP_201_CREATED)

        except Room.DoesNotExist:
            return Response({'error': 'Room not found'}, status=404)
        except Exception as e:
            return Response({'error': str(e)}, status=500)
