# Generated manually

from django.db import migrations, models
import django.db.models.deletion
import uuid
import apps.services.models


class Migration(migrations.Migration):

    dependencies = [
        ('services', '0001_init'),
    ]

    operations = [
        migrations.CreateModel(
            name='ServiceImage',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('image', models.ImageField(help_text='Изображение услуги (JPG, PNG, GIF, WEBP до 5MB)', max_length=500, upload_to=apps.services.models.service_image_upload_path)),
                ('order', models.IntegerField(default=0, help_text='Порядок отображения')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('service', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='images', to='services.service')),
            ],
            options={
                'db_table': 'service_images',
                'ordering': ['order', 'created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='serviceimage',
            index=models.Index(fields=['service', 'order'], name='service_ima_service_idx'),
        ),
    ]
