# Generated manually

import apps.services.models
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('services', '0002_serviceimage'),
    ]

    operations = [
        migrations.CreateModel(
            name='DealDeliveryAttachment',
            fields=[
                (
                    'id',
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    'file',
                    models.FileField(
                        help_text='Файл результата работы (до 20MB)',
                        max_length=500,
                        upload_to=apps.services.models.deal_delivery_upload_path,
                    ),
                ),
                ('filename', models.CharField(max_length=255)),
                ('file_size', models.IntegerField()),
                ('content_type', models.CharField(blank=True, max_length=100)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                (
                    'deal',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='delivery_attachments',
                        to='services.deal',
                    ),
                ),
            ],
            options={
                'db_table': 'deal_delivery_attachments',
                'ordering': ['created_at'],
            },
        ),
    ]
