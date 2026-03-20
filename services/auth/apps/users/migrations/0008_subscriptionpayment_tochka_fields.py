# services/auth/apps/users/migrations/0008_subscriptionpayment_tochka_fields.py
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0007_ff'),
    ]

    operations = [
        # operationId от Точки — нужен для GET /status
        migrations.AddField(
            model_name='subscriptionpayment',
            name='tochka_operation_id',
            field=models.CharField(
                max_length=255,
                blank=True,
                null=True,
                help_text='ID операции в системе Точка Банка (operationId)'
            ),
        ),
        # consumerId — ID покупателя в Точке для повторных списаний
        migrations.AddField(
            model_name='subscriptionpayment',
            name='tochka_consumer_id',
            field=models.CharField(
                max_length=255,
                blank=True,
                null=True,
                help_text='ID покупателя в системе Точка Банка (consumerId)'
            ),
        ),
        # Ссылка на оплату — отдаётся пользователю
        migrations.AddField(
            model_name='subscriptionpayment',
            name='payment_link',
            field=models.URLField(
                max_length=1000,
                blank=True,
                null=True,
                help_text='Ссылка на страницу оплаты Точка Банк'
            ),
        ),
        # Последний статус от Точки
        migrations.AddField(
            model_name='subscriptionpayment',
            name='tochka_status',
            field=models.CharField(
                max_length=50,
                blank=True,
                null=True,
                help_text='Статус подписки в системе Точки (Active/Pending/Cancelled/...)'
            ),
        ),
    ]
