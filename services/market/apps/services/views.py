from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import Service, Order
from .serializers import (
    ServiceSerializer, 
    OrderSerializer, 
    GenerateTZSerializer, 
    CreateOrderSerializer
)
from .services import AIService, OrderService


class ServiceViewSet(viewsets.ModelViewSet):
    queryset = Service.objects.all()
    serializer_class = ServiceSerializer
    
    def get_permissions(self):
        """
        Просмотр доступен всем, создание/редактирование - только авторизованным
        """
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_queryset(self):
        """
        Поддержка фильтрации по owner_id для секции "Мои услуги"
        """
        queryset = Service.objects.all()
        owner_id = self.request.query_params.get('owner_id')
        if owner_id:
            queryset = queryset.filter(owner_id=owner_id)
        return queryset

    def list(self, request):
        """Получить все услуги (с опциональной фильтрацией)"""
        services = self.get_queryset()
        serializer = self.get_serializer(services, many=True)
        
        return Response({
            'status': 'success',
            'data': serializer.data,
            'error': None
        }, status=status.HTTP_200_OK)

    def retrieve(self, request, pk=None):
        """Получить одну услугу"""
        try:
            service = self.get_object()
            serializer = self.get_serializer(service)
            
            return Response({
                'status': 'success',
                'data': serializer.data,
                'error': None
            }, status=status.HTTP_200_OK)
            
        except Service.DoesNotExist:
            return Response({
                'status': 'error',
                'error': 'Услуга не найдена',
                'data': None
            }, status=status.HTTP_404_NOT_FOUND)

    def create(self, request, *args, **kwargs):
        """
        Создать новую услугу с автоматическим назначением владельца
        """
        serializer = self.get_serializer(data=request.data)
        
        if not serializer.is_valid():
            return Response({
                'status': 'error',
                'error': serializer.errors,
                'data': None
            }, status=status.HTTP_400_BAD_REQUEST)

        # ID берём из токена (безопасно), имя и аватар - из данных фронта
        serializer.save(
            owner_id=request.user.id,
            owner_name=request.data.get('owner_name', 'Фрилансер'),
            owner_avatar=request.data.get('owner_avatar', '')
        )

        return Response({
            'status': 'success',
            'data': serializer.data,
            'error': None
        }, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        """Обновить услугу (только владелец)"""
        instance = self.get_object()
        
        # Проверка, что пользователь - владелец
        if str(instance.owner_id) != str(request.user.id):
            return Response({
                'status': 'error',
                'error': 'Вы не можете редактировать чужую услугу',
                'data': None
            }, status=status.HTTP_403_FORBIDDEN)
        
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        
        if not serializer.is_valid():
            return Response({
                'status': 'error',
                'error': serializer.errors,
                'data': None
            }, status=status.HTTP_400_BAD_REQUEST)
        
        serializer.save()
        
        return Response({
            'status': 'success',
            'data': serializer.data,
            'error': None
        }, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        """Удалить услугу (только владелец)"""
        instance = self.get_object()
        
        # Проверка, что пользователь - владелец
        if str(instance.owner_id) != str(request.user.id):
            return Response({
                'status': 'error',
                'error': 'Вы не можете удалить чужую услугу',
                'data': None
            }, status=status.HTTP_403_FORBIDDEN)
        
        instance.delete()
        
        return Response({
            'status': 'success',
            'data': {'message': 'Услуга успешно удалена'},
            'error': None
        }, status=status.HTTP_200_OK)


class OrderViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['post'], url_path='preview')
    def preview_tz(self, request):
        """
        Генерация ТЗ с помощью AI
        
        Клиент отправляет свои требования, AI генерирует структурированное ТЗ
        на основе шаблона воркера
        """
        serializer = GenerateTZSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response({
                'status': 'error',
                'error': serializer.errors,
                'data': None
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            generated_tz = AIService.generate_tz(
                service_id=serializer.validated_data['service_id'],
                client_requirements=serializer.validated_data['raw_requirements']
            )
            
            return Response({
                'status': 'success',
                'data': {
                    'generated_tz': generated_tz,
                    'message': 'ТЗ успешно сгенерировано! Вы можете его отредактировать перед отправкой.'
                },
                'error': None
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'status': 'error',
                'error': f'Ошибка генерации ТЗ: {str(e)}',
                'data': None
            }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], url_path='create')
    def create_order(self, request):
        """Создать заказ с согласованным ТЗ"""
        serializer = CreateOrderSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response({
                'status': 'error',
                'error': serializer.errors,
                'data': None
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            order = OrderService.create_order(
                service_id=serializer.validated_data['service_id'],
                client_id=request.user.id,
                agreed_tz=serializer.validated_data['agreed_tz']
            )

            return Response({
                'status': 'success',
                'data': OrderSerializer(order).data,
                'error': None
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response({
                'status': 'error',
                'error': str(e),
                'data': None
            }, status=status.HTTP_400_BAD_REQUEST)

    def list(self, request):
        """Получить заказы пользователя"""
        from django.db.models import Q
        user_id = request.user.id
        
        orders = Order.objects.filter(
            Q(client_id=user_id) | Q(worker_id=user_id)
        )
        serializer = OrderSerializer(orders, many=True)
        
        return Response({
            'status': 'success',
            'data': serializer.data,
            'error': None
        }, status=status.HTTP_200_OK)
