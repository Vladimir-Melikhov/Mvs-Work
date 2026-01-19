# Generated migration for social links

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_add'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='github_link',
            field=models.URLField(blank=True, null=True, help_text='Ссылка на GitHub профиль'),
        ),
        migrations.AddField(
            model_name='profile',
            name='behance_link',
            field=models.URLField(blank=True, null=True, help_text='Ссылка на Behance профиль'),
        ),
    ]
