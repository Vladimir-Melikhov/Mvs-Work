# services/auth/apps/users/management/commands/check_subscriptions.py
import os
import requests
import logging
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from apps.users.models import Subscription, User

logger = logging.getLogger(__name__)

PENDING_STATUSES = (
    'Preparing', 'PREPARING', 'Pending', 'PENDING',
    'Created', 'CREATED', 'Trial', 'TRIAL',
    'PastDue', 'PASTDUE',
)

PAYMENT_GRACE_DAYS = 3


def _deactivate_services_bulk(owner_ids: list):
    if not owner_ids:
        return
    try:
        from apps.users.jwt_service import ServiceJWT
        token = ServiceJWT.generate_service_token('auth-cron', expires_minutes=5)
        market_url = os.getenv('MARKET_SERVICE_URL', 'http://market:8002')
        response = requests.post(
            f"{market_url}/api/market/services/internal-deactivate/",
            headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'},
            json={'owner_ids': owner_ids},
            timeout=10
        )
        if response.status_code == 200:
            count = response.json().get('data', {}).get('deactivated_count', 0)
            logger.info("[CheckSubs] Bulk деактивировано: %d объявлений для %d воркеров", count, len(owner_ids))
    except Exception as e:
        logger.error("[CheckSubs] Ошибка bulk деактивации: %s", e)


def _cancel_in_tochka(operation_id: str):
    try:
        from apps.users.tochka_service import TochkaPaymentService
        tochka = TochkaPaymentService()
        tochka.cancel_subscription(operation_id)
        logger.info("[CheckSubs] Подписка %s отменена в Точке", operation_id)
    except Exception as e:
        logger.error("[CheckSubs] Ошибка отмены в Точке %s: %s", operation_id, e)


class Command(BaseCommand):
    help = 'Проверить истёкшие подписки и деактивировать если нет оплаты'

    def handle(self, *args, **options):
        from apps.users.tochka_service import TochkaPaymentService, TochkaAPIError

        now = timezone.now()
        self.stdout.write(f"[{now}] Проверка подписок...")

        expired = Subscription.objects.filter(
            is_active=True,
            expires_at__lt=now
        ).select_related('user')

        tochka = TochkaPaymentService()
        deactivated_ids = []

        for sub in expired:
            self.stdout.write(f"  Проверяю: {sub.user.email}")

            payment = sub.payments.filter(
                tochka_operation_id__isnull=False
            ).order_by('-created_at').first()

            if payment and payment.tochka_operation_id:
                try:
                    tochka_status = tochka.get_subscription_status(payment.tochka_operation_id)
                    self.stdout.write(f"    Статус в Точке: {tochka_status}")

                    # Активна → продлеваем
                    if tochka_status in ('Active', 'ACTIVE'):
                        sub.activate(duration_days=30)
                        self.stdout.write(f"    ✅ Продлена до {sub.expires_at}")
                        continue

                    # В процессе → даём grace period
                    if tochka_status in PENDING_STATUSES:
                        grace_deadline = sub.expires_at + timedelta(days=PAYMENT_GRACE_DAYS)
                        if now < grace_deadline:
                            self.stdout.write(f"    ⏳ Платёж в процессе, grace до {grace_deadline}")
                            continue
                        else:
                            self.stdout.write(f"    ⌛ Grace period истёк, блокируем")
                            _cancel_in_tochka(payment.tochka_operation_id)

                    # Всё остальное → блокируем
                    else:
                        _cancel_in_tochka(payment.tochka_operation_id)

                except TochkaAPIError as e:
                    # Ошибка запроса → не блокируем, подождём следующего запуска
                    self.stdout.write(f"    ⚠️ Ошибка Точки, пропускаем: {e}")
                    continue

            # Нет operationId → блокируем
            sub.deactivate()
            deactivated_ids.append(str(sub.user_id))
            self.stdout.write(f"    ❌ Деактивирована")

        if deactivated_ids:
            _deactivate_services_bulk(deactivated_ids)

        self.stdout.write(f"✅ Готово. Деактивировано: {len(deactivated_ids)}")

        # Воркеры без активной подписки — деактивировать объявления
        workers_without_sub = list(
            User.objects.filter(role='worker')
            .exclude(subscription__is_active=True)
            .values_list('id', flat=True)
        )

        if workers_without_sub:
            _deactivate_services_bulk([str(uid) for uid in workers_without_sub])

        self.stdout.write(f"✅ Объявления без подписки обработаны.")
