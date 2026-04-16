# services/auth/apps/users/migrations/0009_medusa_recipient.py
"""
Миграция для хранения данных получателя Medusa в профиле воркера.

Каждый воркер = один получатель (recipient) в системе Безопасных сделок.
У получателя может быть несколько карт для выплат.
"""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0008_subscriptionpayment_tochka_fields'),
    ]

    operations = [
        # UUID получателя в Medusa (создаётся один раз при первой безопасной сделке)
        migrations.AddField(
            model_name='profile',
            name='medusa_recipient_ext_id',
            field=models.UUIDField(
                null=True,
                blank=True,
                unique=True,
                help_text='ID получателя в системе Безопасных сделок Точка Банка'
            ),
        ),

        # Статус регистрации в Medusa
        migrations.AddField(
            model_name='profile',
            name='medusa_recipient_registered',
            field=models.BooleanField(
                default=False,
                help_text='Зарегистрирован ли воркер как получатель в Medusa'
            ),
        ),

        # UUID текущей основной карты для выплат
        migrations.AddField(
            model_name='profile',
            name='medusa_card_ext_id',
            field=models.UUIDField(
                null=True,
                blank=True,
                help_text='ID основной карты для выплат в Medusa'
            ),
        ),

        # Маскированный номер карты (для отображения: ****1234)
        migrations.AddField(
            model_name='profile',
            name='medusa_card_masked_pan',
            field=models.CharField(
                max_length=20,
                null=True,
                blank=True,
                help_text='Маскированный номер карты (****1234)'
            ),
        ),

        # Статус: есть ли привязанная карта
        migrations.AddField(
            model_name='profile',
            name='medusa_card_linked',
            field=models.BooleanField(
                default=False,
                help_text='Есть ли привязанная карта для выплат'
            ),
        ),
    ]
