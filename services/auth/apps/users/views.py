from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from .serializers import (
    RegisterSerializer, 
    LoginSerializer, 
    UserSerializer, 
    ProfileSerializer,
    SubscriptionSerializer
)
from .services import AuthService
from .models import User, Subscription, SubscriptionPayment, Service
from django.db import transaction
import requests
import os


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response({
                'status': 'error',
                'error': serializer.errors,
                'data': None
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user, tokens = AuthService.register_user(
                email=serializer.validated_data['email'],
                password=serializer.validated_data['password'],
                role=serializer.validated_data['role']
            )
            
            return Response({
                'status': 'success',
                'data': {
                    'user': UserSerializer(user, context={'request': request}).data,
                    'tokens': tokens
                },
                'error': None
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response({
                'status': 'error',
                'error': str(e),
                'data': None
            }, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response({
                'status': 'error',
                'error': serializer.errors,
                'data': None
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user, tokens = AuthService.login_user(
                email=serializer.validated_data['email'],
                password=serializer.validated_data['password']
            )
            
            return Response({
                'status': 'success',
                'data': {
                    'user': UserSerializer(user, context={'request': request}).data,
                    'tokens': tokens
                },
                'error': None
            }, status=status.HTTP_200_OK)
            
        except ValueError as e:
            return Response({
                'status': 'error',
                'error': str(e),
                'data': None
            }, status=status.HTTP_401_UNAUTHORIZED)


class ProfileView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get(self, request):
        return Response({
            'status': 'success',
            'data': UserSerializer(request.user, context={'request': request}).data,
            'error': None
        }, status=status.HTTP_200_OK)

    @transaction.atomic
    def patch(self, request):
        """Обновление профиля с поддержкой загрузки аватарки"""
        try:
            profile = request.user.profile
            
            serializer = ProfileSerializer(
                profile, 
                data=request.data, 
                partial=True,
                context={'request': request}
            )
            
            if serializer.is_valid():
                serializer.save()
                
                # ✅ СИНХРОНИЗАЦИЯ АВАТАРА: Обновляем owner_avatar во всех объявлениях пользователя
                if 'avatar' in request.data or serializer.validated_data.get('avatar'):
                    avatar_url = request.build_absolute_uri(profile.avatar.url) if profile.avatar else ''
                    
                    # Получаем market service URL из env
                    market_service_url = os.getenv('MARKET_SERVICE_URL', 'http://localhost:8002')
                    
                    try:
                        # Обновляем объявления через внешний API
                        auth_header = request.headers.get('Authorization', '')
                        
                        # Отправляем запрос на обновление аватара в объявлениях
                        update_url = f"{market_service_url}/api/market/services/update-owner-avatar/"
                        
                        requests.post(
                            update_url,
                            headers={
                                'Authorization': auth_header,
                                'Content-Type': 'application/json'
                            },
                            json={
                                'owner_id': str(request.user.id),
                                'owner_avatar': avatar_url
                            },
                            timeout=5
                        )
                    except Exception as e:
                        print(f"⚠️ Не удалось обновить аватар в объявлениях: {e}")
                
                return Response({
                    'status': 'success',
                    'data': UserSerializer(request.user, context={'request': request}).data,
                    'error': None
                }, status=status.HTTP_200_OK)
            
            return Response({
                'status': 'error',
                'error': serializer.errors,
                'data': None
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            return Response({
                'status': 'error',
                'error': str(e),
                'data': None
            }, status=status.HTTP_400_BAD_REQUEST)


class CheckBalanceView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        amount = request.data.get('amount', 0)
        has_balance = AuthService.check_balance(request.user.id, float(amount))

        return Response({
            'status': 'success',
            'data': {'has_balance': has_balance},
            'error': None
        }, status=status.HTTP_200_OK)


class BatchUsersView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Получить публичные данные (имя, аватар) для списка ID"""
        user_ids = request.data.get('user_ids', [])
        users = User.objects.filter(id__in=list(set(user_ids)))
        
        data = []
        for user in users:
            try:
                profile = user.profile
                display_name = profile.company_name or profile.full_name or user.email.split('@')[0]
                
                avatar_url = None
                if profile.avatar:
                    avatar_url = request.build_absolute_uri(profile.avatar.url)
                
            except:
                display_name = "Unknown User"
                avatar_url = None
            
            data.append({
                'id': str(user.id),
                'name': display_name,
                'avatar': avatar_url,
                'role': user.role
            })
            
        return Response({'status': 'success', 'data': data})


class PublicProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, user_id):
        """Получить публичный профиль пользователя"""
        try:
            user = User.objects.get(id=user_id)
            profile = user.profile
            
            data = {
                'id': str(user.id),
                'email': user.email,
                'role': user.role,
                'created_at': user.created_at,
                'profile': {
                    'full_name': profile.full_name,
                    'company_name': profile.company_name,
                    'headline': profile.headline,
                    'company_website': profile.company_website,
                    'avatar_url': request.build_absolute_uri(profile.avatar.url) if profile.avatar else None,
                    'bio': profile.bio,
                    'skills': profile.skills,
                    'rating': str(profile.rating),
                    'github_link': profile.github_link,
                    'behance_link': profile.behance_link,
                }
            }
            
            return Response({
                'status': 'success',
                'data': data,
                'error': None
            }, status=status.HTTP_200_OK)
            
        except User.DoesNotExist:
            return Response({
                'status': 'error',
                'error': 'Пользователь не найден',
                'data': None
            }, status=status.HTTP_404_NOT_FOUND)


class SubscriptionView(APIView):
    """Управление подпиской"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Получить информацию о подписке"""
        if request.user.role != 'worker':
            return Response({
                'status': 'error',
                'error': 'Подписка доступна только для воркеров',
                'data': None
            }, status=status.HTTP_403_FORBIDDEN)

        try:
            subscription = request.user.subscription
            # Проверяем и обновляем статус
            subscription.check_and_update_status()
            
            return Response({
                'status': 'success',
                'data': SubscriptionSerializer(subscription).data,
                'error': None
            })
        except Subscription.DoesNotExist:
            # Создаем подписку если её нет
            subscription = Subscription.objects.create(user=request.user, is_active=False)
            return Response({
                'status': 'success',
                'data': SubscriptionSerializer(subscription).data,
                'error': None
            })

    @transaction.atomic
    def post(self, request):
        """Оплатить подписку (заглушка)"""
        if request.user.role != 'worker':
            return Response({
                'status': 'error',
                'error': 'Подписка доступна только для воркеров',
                'data': None
            }, status=status.HTTP_403_FORBIDDEN)

        try:
            subscription = request.user.subscription
        except Subscription.DoesNotExist:
            subscription = Subscription.objects.create(user=request.user, is_active=False)

        # Создаем платеж
        payment = SubscriptionPayment.objects.create(
            subscription=subscription,
            amount=Subscription.SUBSCRIPTION_PRICE,
            status='pending',
            payment_provider='stub'
        )

        # ЗАГЛУШКА: Автоматически подтверждаем оплату
        payment.status = 'completed'
        payment.save()

        # Активируем подписку на 30 дней
        subscription.activate(duration_days=30)

        return Response({
            'status': 'success',
            'data': {
                'subscription': SubscriptionSerializer(subscription).data,
                'payment': {
                    'id': str(payment.id),
                    'amount': str(payment.amount),
                    'status': payment.status
                }
            },
            'message': 'Подписка успешно активирована на 30 дней',
            'error': None
        })
