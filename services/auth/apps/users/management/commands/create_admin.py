# services/auth/apps/users/management/commands/create_admin.py
"""
Команда для создания администратора маркетплейса.

Использование:
    python manage.py create_admin --email admin@example.com --password secret123

Или через переменные окружения:
    ADMIN_EMAIL=admin@example.com ADMIN_PASSWORD=secret123 python manage.py create_admin
"""
import os
from django.core.management.base import BaseCommand, CommandError
from apps.users.models import User, Profile, Wallet


class Command(BaseCommand):
    help = 'Создать администратора маркетплейса'

    def add_arguments(self, parser):
        parser.add_argument('--email', type=str, help='Email администратора')
        parser.add_argument('--password', type=str, help='Пароль администратора')
        parser.add_argument('--no-input', action='store_true', help='Не задавать вопросы')

    def handle(self, *args, **options):
        email = options.get('email') or os.getenv('ADMIN_EMAIL')
        password = options.get('password') or os.getenv('ADMIN_PASSWORD')

        if not email:
            if options.get('no_input'):
                raise CommandError('Укажите --email или переменную ADMIN_EMAIL')
            email = input('Email администратора: ').strip()

        if not password:
            if options.get('no_input'):
                raise CommandError('Укажите --password или переменную ADMIN_PASSWORD')
            import getpass
            password = getpass.getpass('Пароль: ')

        if not email or not password:
            raise CommandError('Email и пароль обязательны')

        if len(password) < 8:
            raise CommandError('Пароль должен быть не менее 8 символов')

        if User.objects.filter(email=email).exists():
            user = User.objects.get(email=email)
            user.is_staff = True
            user.is_superuser = True
            user.is_active = True
            user.email_verified = True
            user.role = 'admin'
            user.set_password(password)
            user.save()

            # Убеждаемся что профиль и кошелёк есть
            Profile.objects.get_or_create(user=user)
            Wallet.objects.get_or_create(user=user)

            self.stdout.write(
                self.style.SUCCESS(f'✅ Пользователь {email} обновлён до суперадмина')
            )
        else:
            user = User.objects.create_superuser(email=email, password=password)
            self.stdout.write(
                self.style.SUCCESS(f'✅ Суперадмин {email} создан успешно')
            )

        self.stdout.write(f'   Доступ к админке: http://localhost:8001/admin/')
