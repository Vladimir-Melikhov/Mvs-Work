# Generated migration for subscription models

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Subscription',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('is_active', models.BooleanField(db_index=True, default=False)),
                ('started_at', models.DateTimeField(blank=True, null=True)),
                ('expires_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='subscription', to='users.user')),
            ],
            options={
                'db_table': 'subscriptions',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='SubscriptionPayment',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('amount', models.DecimalField(decimal_places=2, default=444.0, max_digits=10)),
                ('status', models.CharField(choices=[('pending', 'Ожидает оплаты'), ('completed', 'Оплачено'), ('failed', 'Ошибка')], default='pending', max_length=20)),
                ('payment_provider', models.CharField(default='stub', max_length=50)),
                ('external_payment_id', models.CharField(blank=True, max_length=255, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('subscription', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='payments', to='users.subscription')),
            ],
            options={
                'db_table': 'subscription_payments',
                'ordering': ['-created_at'],
            },
        ),
    ]
