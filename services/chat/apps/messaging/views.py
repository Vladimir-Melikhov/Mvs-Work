from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
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
        
        room = Room.objects.create(
            members=serializer.validated_data['member_ids']
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
