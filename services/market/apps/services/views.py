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
    permission_classes = [AllowAny]

    def list(self, request):
        """Get all services"""
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


class OrderViewSet(viewsets.ViewSet):
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
                client_id=str(request.user.id),
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
        orders = Order.objects.filter(client_id=request.user.id)
        serializer = OrderSerializer(orders, many=True)
        
        return Response({
            'status': 'success',
            'data': serializer.data,
            'error': None
        }, status=status.HTTP_200_OK)
