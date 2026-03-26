# services/auth/apps/users/webhook_views.py
"""
Обработчик вебхуков от Точка Банка.

Точка шлёт POST с Content-Type: text/plain, тело — JWT-токен (RS256).
Мы декодируем его без верификации подписи (доверяем Точке по сети),
извлекаем operationId и обновляем подписку.
"""
import logging
import jwt
import os
import requests

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.utils import timezone

logger = logging.getLogger(__name__)


def _deactivate_services(user_id: str):
    """Деактивировать объявления воркера через market service."""
    try:
        from .jwt_service import ServiceJWT
        token = ServiceJWT.generate_service_token('auth-webhook', expires_minutes=5)
        market_url = os.getenv('MARKET_SERVICE_URL', 'http://market:8002')
        response = requests.post(
            f"{market_url}/api/market/services/internal-deactivate/",
            headers={
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json',
            },
            json={'owner_id': str(user_id)},
            timeout=5
        )
        if response.status_code == 200:
            count = response.json().get('data', {}).get('deactivated_count', 0)
            logger.info("[Webhook] Деактивировано объявлений для %s: %d", user_id, count)
        else:
            logger.warning("[Webhook] market вернул %s для %s", response.status_code, user_id)
    except Exception as e:
        logger.error("[Webhook] Ошибка деактивации объявлений для %s: %s", user_id, e)


class TochkaWebhookView(APIView):
    """
    POST /api/auth/webhook/tochka/

    Принимает JWT-токен от Точки, декодирует, обрабатывает событие оплаты.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        # Точка шлёт text/plain — тело это и есть JWT
        raw_body = request.body.decode('utf-8', errors='replace').strip()

        if not raw_body:
            logger.warning("[Webhook] Пустое тело запроса")
            return Response({'status': 'ok'})  # Всегда 200 чтобы Точка не ретраила зря

        # Декодируем JWT без верификации подписи (алгоритм RS256, публичный ключ не храним)
        try:
            payload = jwt.decode(
                raw_body,
                options={"verify_signature": False},
                algorithms=["RS256", "HS256"],
            )
        except Exception as e:
            logger.error("[Webhook] Не удалось декодировать JWT: %s", e)
            return Response({'status': 'ok'})

        logger.info("[Webhook] Получен вебхук от Точки: %s", payload)

        event_type = payload.get('event') or payload.get('type') or ''
        operation_id = (
            payload.get('operationId') or
            payload.get('Data', {}).get('operationId') or
            payload.get('data', {}).get('operationId') or
            ''
        )
        tochka_status = (
            payload.get('status') or
            payload.get('Data', {}).get('status') or
            payload.get('data', {}).get('status') or
            ''
        )

        if not operation_id:
            logger.warning("[Webhook] operationId не найден в payload: %s", payload)
            return Response({'status': 'ok'})

        self._handle_payment(operation_id, tochka_status, payload)
        return Response({'status': 'ok'})

    def _handle_payment(self, operation_id: str, tochka_status: str, payload: dict):
        from .models import SubscriptionPayment, Subscription
        from datetime import timedelta

        # Ищем платёж по operationId
        try:
            payment = SubscriptionPayment.objects.select_related(
                'subscription__user'
            ).get(tochka_operation_id=operation_id)
        except SubscriptionPayment.DoesNotExist:
            logger.warning("[Webhook] Платёж с operationId=%s не найден", operation_id)
            return
        except SubscriptionPayment.MultipleObjectsReturned:
            payment = SubscriptionPayment.objects.filter(
                tochka_operation_id=operation_id
            ).select_related('subscription__user').latest('created_at')

        subscription = payment.subscription
        user = subscription.user

        logger.info(
            "[Webhook] Обрабатываем платёж %s, статус=%s, user=%s",
            operation_id, tochka_status, user.email
        )

        # Обновляем статус платежа
        payment.tochka_status = tochka_status
        payment.save(update_fields=['tochka_status'])

        # Успешная оплата → +30 дней к подписке
        if tochka_status in ('Active', 'Paid', 'PAID', 'ACTIVE', 'Completed', 'COMPLETED'):
            payment.status = 'completed'
            payment.save(update_fields=['status', 'tochka_status'])
            subscription.activate(duration_days=30)
            logger.info(
                "[Webhook] ✅ Подписка активирована/продлена для %s до %s",
                user.email, subscription.expires_at
            )
            return

        # Любой неуспешный статус → сразу деактивируем подписку и объявления
        # (Точка не будет списывать — мы сами отключаем)
        if tochka_status in ('Cancelled', 'CANCELLED', 'Failed', 'FAILED',
                              'Inactive', 'INACTIVE', 'Expired', 'EXPIRED',
                              'Refused', 'REFUSED', 'Rejected', 'REJECTED',
                              'Suspended', 'SUSPENDED'):
            payment.status = 'failed'
            payment.save(update_fields=['status', 'tochka_status'])

            if subscription.is_active:
                subscription.deactivate()
                logger.info("[Webhook] Подписка деактивирована для %s (статус=%s)", user.email, tochka_status)
                _deactivate_services(user.id)
