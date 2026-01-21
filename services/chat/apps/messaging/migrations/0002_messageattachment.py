# Generated manually

import apps.messaging.models
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('messaging', '0001_initiadl'),
    ]

    operations = [
        migrations.CreateModel(
            name='MessageAttachment',
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
                        help_text='Файл-вложение (до 20MB)',
                        max_length=500,
                        upload_to=apps.messaging.models.message_attachment_upload_path,
                    ),
                ),
                (
                    'filename',
                    models.CharField(help_text='Оригинальное имя файла', max_length=255),
                ),
                (
                    'file_size',
                    models.IntegerField(help_text='Размер файла в байтах'),
                ),
                ('content_type', models.CharField(blank=True, max_length=100)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                (
                    'message',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='attachments',
                        to='messaging.message',
                    ),
                ),
            ],
            options={
                'db_table': 'message_attachments',
                'ordering': ['created_at'],
            },
        ),
    ]
