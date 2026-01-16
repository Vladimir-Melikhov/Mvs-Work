# Generated migration for avatar ImageField

from django.db import migrations, models
import apps.users.models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),  # Замените на номер вашей последней миграции
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='avatar',
            field=models.ImageField(
                blank=True,
                help_text='Аватар пользователя (JPG, PNG, GIF до 5MB)',
                max_length=500,
                null=True,
                upload_to=apps.users.models.avatar_upload_path
            ),
        ),
    ]
