# services/market/apps/services/migrations/0010_medusa_integration.py
"""
Миграция для интеграции с Безопасными сделками Точка Банка (Medusa).

Добавляет поля:
  - Deal: medusa_order_ext_id, medusa_service_ext_id, medusa_payment_url,
          medusa_order_status, medusa_commission_*
  - Profile (через auth service): medusa_recipient_ext_id, medusa_card_ext_id
  
Приоритет: не ломать существующий функционал — все поля nullable.
"""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('services', '0009_deal_is_escrow'),
    ]

    operations = [
        # ── Deal: привязка к заказу в Medusa ──────────────────────────────────

        # UUID заказа в системе Medusa (= order_ext_id)
        migrations.AddField(
            model_name='deal',
            name='medusa_order_ext_id',
            field=models.UUIDField(
                null=True,
                blank=True,
                db_index=True,
                help_text='ID заказа в системе Безопасных сделок Точка Банка'
            ),
        ),

        # UUID услуги внутри заказа Medusa (нужен для Make Decision)
        migrations.AddField(
            model_name='deal',
            name='medusa_service_ext_id',
            field=models.UUIDField(
                null=True,
                blank=True,
                help_text='ID услуги в заказе Medusa (для принятия решения)'
            ),
        ),

        # Ссылка на оплату от Medusa (отдаётся заказчику)
        migrations.AddField(
            model_name='deal',
            name='medusa_payment_url',
            field=models.URLField(
                max_length=1000,
                null=True,
                blank=True,
                help_text='Ссылка на страницу оплаты от Точка Банка'
            ),
        ),

        # Статус заказа в Medusa (created/paid/completed/cancelled)
        migrations.AddField(
            model_name='deal',
            name='medusa_order_status',
            field=models.CharField(
                max_length=30,
                null=True,
                blank=True,
                help_text='Статус заказа в системе Medusa'
            ),
        ),

        # ── Комиссии (сохраняем для отображения и аудита) ─────────────────────

        # Комиссия платформы MVS-Work
        migrations.AddField(
            model_name='deal',
            name='medusa_platform_commission',
            field=models.DecimalField(
                max_digits=10,
                decimal_places=2,
                null=True,
                blank=True,
                help_text='Комиссия платформы MVS-Work (0.5%)'
            ),
        ),

        # Комиссия Безопасных сделок (Точки)
        migrations.AddField(
            model_name='deal',
            name='medusa_tochka_commission',
            field=models.DecimalField(
                max_digits=10,
                decimal_places=2,
                null=True,
                blank=True,
                help_text='Комиссия Безопасных сделок (0.8%)'
            ),
        ),

        # Комиссия за эквайринг
        migrations.AddField(
            model_name='deal',
            name='medusa_acquiring_commission',
            field=models.DecimalField(
                max_digits=10,
                decimal_places=2,
                null=True,
                blank=True,
                help_text='Комиссия за эквайринг (2.2%)'
            ),
        ),

        # Итого комиссия (передаётся в Data.Services[].comission)
        migrations.AddField(
            model_name='deal',
            name='medusa_total_commission',
            field=models.DecimalField(
                max_digits=10,
                decimal_places=2,
                null=True,
                blank=True,
                help_text='Суммарная комиссия по сделке'
            ),
        ),

        # Итого к оплате заказчиком (цена + все комиссии)
        migrations.AddField(
            model_name='deal',
            name='medusa_total_amount',
            field=models.DecimalField(
                max_digits=10,
                decimal_places=2,
                null=True,
                blank=True,
                help_text='Итого к оплате заказчиком (цена + комиссии)'
            ),
        ),

        # UUID получателя (recipient_ext_id) — ID воркера в системе Medusa
        migrations.AddField(
            model_name='deal',
            name='medusa_recipient_ext_id',
            field=models.UUIDField(
                null=True,
                blank=True,
                help_text='ID получателя (воркера) в системе Medusa'
            ),
        ),

        # UUID карты получателя (card_ext_id)
        migrations.AddField(
            model_name='deal',
            name='medusa_card_ext_id',
            field=models.UUIDField(
                null=True,
                blank=True,
                help_text='ID карты получателя в системе Medusa'
            ),
        ),
    ]