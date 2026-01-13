# Generated migration for dispute system

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('services', '0001_initial'),
    ]

    operations = [
        # Добавляем новый статус 'dispute'
        migrations.AlterField(
            model_name='deal',
            name='status',
            field=models.CharField(
                max_length=30,
                choices=[
                    ('pending', 'Ожидает оплаты'),
                    ('paid', 'Оплачен, в работе'),
                    ('delivered', 'Сдан на проверку'),
                    ('dispute', 'В споре'),
                    ('completed', 'Завершён'),
                    ('cancelled', 'Отменён'),
                ],
                default='pending'
            ),
        ),
        
        # Добавляем поля для диспута
        migrations.AddField(
            model_name='deal',
            name='dispute_client_reason',
            field=models.TextField(blank=True, help_text='Претензия клиента'),
        ),
        migrations.AddField(
            model_name='deal',
            name='dispute_worker_defense',
            field=models.TextField(blank=True, help_text='Защита исполнителя'),
        ),
        migrations.AddField(
            model_name='deal',
            name='dispute_created_at',
            field=models.DateTimeField(null=True, blank=True, help_text='Когда открыт спор'),
        ),
        migrations.AddField(
            model_name='deal',
            name='dispute_resolved_at',
            field=models.DateTimeField(null=True, blank=True, help_text='Когда разрешен спор'),
        ),
        migrations.AddField(
            model_name='deal',
            name='dispute_winner',
            field=models.CharField(
                max_length=10,
                blank=True,
                choices=[('client', 'Клиент'), ('worker', 'Исполнитель')],
                help_text='Кто выиграл спор'
            ),
        ),
        
        # Обновляем constraint для включения статуса 'dispute'
        migrations.RemoveConstraint(
            model_name='deal',
            name='unique_active_deal_per_pair',
        ),
        migrations.AddConstraint(
            model_name='deal',
            constraint=models.UniqueConstraint(
                fields=['client_id', 'worker_id'],
                condition=models.Q(status__in=['pending', 'paid', 'delivered', 'dispute']),
                name='unique_active_deal_per_pair'
            ),
        ),
    ]
