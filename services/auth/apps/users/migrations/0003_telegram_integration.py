# Generated migration for Telegram integration

from django.db import migrations, models
import django.db.models.deletion
from django.utils import timezone
from datetime import timedelta


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_subscription'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='telegram_chat_id',
            field=models.BigIntegerField(
                blank=True,
                help_text='Telegram Chat ID для уведомлений',
                null=True,
                unique=True,
            ),
        ),
        migrations.AddField(
            model_name='profile',
            name='telegram_notifications_enabled',
            field=models.BooleanField(
                default=False,
                help_text='Включены ли Telegram уведомления',
            ),
        ),
        migrations.CreateModel(
            name='TelegramLinkToken',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('token', models.CharField(db_index=True, max_length=64, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('expires_at', models.DateTimeField()),
                ('used', models.BooleanField(default=False)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='telegram_tokens', to='users.user')),
            ],
            options={
                'db_table': 'telegram_link_tokens',
                'ordering': ['-created_at'],
            },
        ),
    ]
