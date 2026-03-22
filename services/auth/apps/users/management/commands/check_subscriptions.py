# services/auth/apps/users/management/commands/check_subscriptions.py
import os
import requests
import logging
from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.users.models import Subscription, User

logger = logging.getLogger(__name__)


def _deactivate_services_in_market(user_id: str):
    try:
        from apps.users.jwt_service import ServiceJWT
        token = ServiceJWT.generate_service_token('auth-cron', expires_minutes=5)

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
            data = response.json()
            count = data.get('data', {}).get('deactivated_count', 0)
            logger.info("[CheckSubs] Деактивировано объявлений для %s: %d", user_id, count)
        else:
            logger.warning("[CheckSubs] market вернул %s для %s", response.status_code, user_id)
    except Exception as e:
        logger.error("[CheckSubs] Ошибка деактивации объявлений для %s: %s", user_id, e)


def _deactivate_services_bulk(owner_ids: list):
    """Деактивировать объявления сразу для списка воркеров (один запрос)"""
    if not owner_ids:
        return
    try:
        from apps.users.jwt_service import ServiceJWT
        token = ServiceJWT.generate_service_token('auth-cron', expires_minutes=5)

        market_url = os.getenv('MARKET_SERVICE_URL', 'http://market:8002')
        response = requests.post(
            f"{market_url}/api/market/services/internal-deactivate/",
            headers={
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json',
            },
            json={'owner_ids': owner_ids},
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            count = data.get('data', {}).get('deactivated_count', 0)
            logger.info("[CheckSubs] Bulk деактивировано объявлений: %d для %d воркеров", count, len(owner_ids))
        else:
            logger.warning("[CheckSubs] market bulk вернул %s", response.status_code)
    except Exception as e:
        logger.error("[CheckSubs] Ошибка bulk деактивации: %s", e)


class Command(BaseCommand):
    help = 'Проверить и деактивировать истёкшие подписки, деактивировать их объявления'

    def handle(self, *args, **options):
        now = timezone.now()
        self.stdout.write(f"[{now}] Проверка подписок...")

        # 1. Истёкшие подписки
        expired = Subscription.objects.filter(
            is_active=True,
            expires_at__lt=now
        ).select_related('user')

        count = expired.count()
        self.stdout.write(f"Найдено истёкших подписок: {count}")

        for sub in expired:
            self.stdout.write(f"  Деактивирую: {sub.user.email}")
            sub.deactivate()
            _deactivate_services_in_market(sub.user_id)

        self.stdout.write(f"✅ Истёкшие подписки обработаны: {count}")

        # 2. Воркеры без активной подписки — деактивировать их объявления
        workers_without_sub = list(
            User.objects.filter(role='worker')
            .exclude(subscription__is_active=True)
            .values_list('id', flat=True)
        )

        self.stdout.write(f"Воркеров без активной подписки: {len(workers_without_sub)}")

        if workers_without_sub:
            _deactivate_services_bulk([str(uid) for uid in workers_without_sub])

        self.stdout.write(f"✅ Готово.")
