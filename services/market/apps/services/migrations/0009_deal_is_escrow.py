# services/market/apps/services/migrations/0009_deal_is_escrow.py
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('services', '0008_deal_dispute_winner_default'),
    ]

    operations = [
        migrations.AddField(
            model_name='deal',
            name='is_escrow',
            field=models.BooleanField(
                default=True,
                help_text='Безопасная сделка (с холдированием средств)'
            ),
        ),
        # Новый статус для неэскроу-флоу: исполнитель принял, работа идёт без оплаты
        migrations.AlterField(
            model_name='deal',
            name='status',
            field=models.CharField(
                max_length=30,
                choices=[
                    ('pending', 'Ожидает оплаты'),
                    ('accepted', 'Принят исполнителем (без эскроу)'),
                    ('paid', 'Оплачен, в работе'),
                    ('delivered', 'Сдан на проверку'),
                    ('dispute', 'В споре'),
                    ('completed', 'Завершён'),
                    ('cancelled', 'Отменён'),
                ],
                default='pending',
            ),
        ),
    ]
