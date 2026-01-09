from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('services', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='deal',
            name='dispute_status',
            field=models.CharField(
                choices=[
                    ('none', 'Нет спора'),
                    ('requested', 'Спор открыт'),
                    ('resolved', 'Спор разрешён'),
                ],
                default='none',
                help_text='Статус спора для безопасной отмены',
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name='deal',
            name='dispute_reason',
            field=models.TextField(blank=True, help_text='Причина открытия спора'),
        ),
        migrations.AddField(
            model_name='deal',
            name='dispute_initiator_id',
            field=models.UUIDField(blank=True, help_text='Кто открыл спор', null=True),
        ),
        migrations.AddField(
            model_name='deal',
            name='dispute_created_at',
            field=models.DateTimeField(blank=True, help_text='Когда открыт спор', null=True),
        ),
    ]
