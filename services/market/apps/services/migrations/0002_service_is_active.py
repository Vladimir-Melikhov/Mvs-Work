from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('services', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='service',
            name='is_active',
            field=models.BooleanField(
                db_index=True, 
                default=True, 
                help_text='Активно ли объявление (требует активной подписки)'
            ),
        ),
        migrations.AddIndex(
            model_name='service',
            index=models.Index(fields=['is_active', '-created_at'], name='services_is_active_idx'),
        ),
    ]
