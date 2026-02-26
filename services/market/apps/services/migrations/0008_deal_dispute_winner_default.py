# services/market/apps/services/migrations/0008_deal_dispute_winner_default.py
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('services', '0007_deal_was_delivered'),
    ]

    operations = [
        migrations.AlterField(
            model_name='deal',
            name='dispute_winner',
            field=models.CharField(
                max_length=10,
                blank=True,
                default='',
                choices=[('client', 'Клиент'), ('worker', 'Исполнитель')],
                help_text='Кто выиграл спор'
            ),
        ),
    ]