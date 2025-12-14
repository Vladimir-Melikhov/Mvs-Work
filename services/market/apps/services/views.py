from rest_framework import viewsets, status, permissions
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
    
    # === ГЛАВНОЕ ИСПРАВЛЕНИЕ ===
    # 1. Отключаем проверку токена для GET запросов. 
    # Сервер даже не будет пытаться читать токен, поэтому ошибки 401 не будет.
    def get_authenticators(self):
        if self.request.method == 'GET':
            return []
        return super().get_authenticators()

    # 2. Настраиваем права доступа
    def get_permissions(self):
        # Для создания/изменения/удаления — строго по токену
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated()]
        # Для просмотра (list, retrieve) — пускаем всех (AllowAny)
        return [AllowAny()]
    # ===========================

    def get_queryset(self):
        """
        Support filtering by owner_id for 'My Services' section
        """
        queryset = Service.objects.all()
        owner_id = self.request.query_params.get('owner_id')
        if owner_id:
            queryset = queryset.filter(owner_id=owner_id)
        return queryset

    def list(self, request):
        """Get all services (with optional filtering)"""
        services = self.get_queryset()
        serializer = self.get_serializer(services, many=True)
        
        return Response({
            'status': 'success',
            'data': serializer.data,
            'error': None
        }, status=status.HTTP_200_OK)

    def retrieve(self, request, pk=None):
        """Get single service"""
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
                'error': 'Service not found',
                'data': None
            }, status=status.HTTP_404_NOT_FOUND)

    def create(self, request, *args, **kwargs):
        """
        Create a new service with automatic owner assignment
        """
        serializer = self.get_serializer(data=request.data)
        
        if not serializer.is_valid():
            return Response({
                'status': 'error',
                'error': serializer.errors,
                'data': None
            }, status=status.HTTP_400_BAD_REQUEST)

        # Здесь мы берем ID юзера из токена (безопасно),
        # а имя и аватар — из данных, присланных фронтом
        serializer.save(
            owner_id=request.user.id,
            owner_name=request.data.get('owner_name', 'Freelancer'),
            owner_avatar=request.data.get('owner_avatar', '')
        )

        return Response({
            'status': 'success',
            'data': serializer.data,
            'error': None
        }, status=status.HTTP_201_CREATED)


class OrderViewSet(viewsets.ViewSet):
    # Для заказов оставляем строгую проверку всегда
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['post'], url_path='preview')
    def preview_tz(self, request):
        """Generate TZ preview using AI"""
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
                'data': {'generated_tz': generated_tz},
                'error': None
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'status': 'error',
                'error': str(e),
                'data': None
            }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], url_path='create')
    def create_order(self, request):
        """Create order with agreed TZ"""
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
        """Get user orders"""
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