# services/auth/apps/users/management/commands/register_webhook.py
import os
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Зарегистрировать вебхук в Точка Банке'

    def handle(self, *args, **options):
        from apps.users.tochka_service import TochkaPaymentService

        frontend_url = os.getenv('FRONTEND_URL', 'https://mvs-work.ru')
        webhook_url = f"{frontend_url.rstrip('/')}/api/auth/webhook/tochka/"

        self.stdout.write(f"Регистрируем вебхук: {webhook_url}")

        tochka = TochkaPaymentService()
        success = tochka.register_webhook(webhook_url)

        if success:
            self.stdout.write(self.style.SUCCESS('✅ Вебхук зарегистрирован'))
        else:
            self.stdout.write(self.style.ERROR('❌ Ошибка регистрации'))
