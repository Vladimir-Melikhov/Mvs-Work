# services/market/apps/services/migrations/0007_deal_was_delivered.py
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('services', '0006_favorite_service_services_price_e2d79c_idx_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='deal',
            name='was_delivered',
            field=models.BooleanField(
                default=False,
                help_text='Была ли работа хотя бы раз сдана (для контроля отмены)'
            ),
        ),
    ]