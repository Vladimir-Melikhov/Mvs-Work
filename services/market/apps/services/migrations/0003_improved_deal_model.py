from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("services", "0002_deal_cancellation_reason_deal_cancelled_by_and_more"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="deal",
            name="client_confirmed",
        ),
        migrations.RemoveField(
            model_name="deal",
            name="worker_confirmed",
        ),
        migrations.RemoveField(
            model_name="deal",
            name="activated_at",
        ),
        migrations.RemoveField(
            model_name="deal",
            name="completion_requested_by",
        ),
        migrations.RemoveField(
            model_name="deal",
            name="completion_requested_at",
        ),
        migrations.AddField(
            model_name="deal",
            name="client_agreed",
            field=models.BooleanField(default=False, help_text="Клиент согласен с условиями"),
        ),
        migrations.AddField(
            model_name="deal",
            name="worker_agreed",
            field=models.BooleanField(default=False, help_text="Воркер согласен с условиями"),
        ),
        migrations.AddField(
            model_name="deal",
            name="payment_completed",
            field=models.BooleanField(default=False, help_text="Оплата прошла"),
        ),
        migrations.AddField(
            model_name="deal",
            name="payment_completed_at",
            field=models.DateTimeField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name="deal",
            name="delivered_at",
            field=models.DateTimeField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name="deal",
            name="delivery_message",
            field=models.TextField(blank=True, help_text="Сообщение воркера при сдаче"),
        ),
        migrations.AddField(
            model_name="deal",
            name="completion_message",
            field=models.TextField(blank=True, help_text="Отзыв клиента"),
        ),
        migrations.AddField(
            model_name="deal",
            name="change_request_by",
            field=models.UUIDField(null=True, blank=True, help_text="Кто запросил изменение условий"),
        ),
        migrations.AddField(
            model_name="deal",
            name="change_request_reason",
            field=models.TextField(blank=True, help_text="Причина запроса изменений"),
        ),
        migrations.AddField(
            model_name="deal",
            name="change_request_pending",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="deal",
            name="revision_count",
            field=models.IntegerField(default=0, help_text="Сколько раз запрашивались правки"),
        ),
        migrations.AddField(
            model_name="deal",
            name="max_revisions",
            field=models.IntegerField(default=3, help_text="Максимум бесплатных доработок"),
        ),
        migrations.AddField(
            model_name="deal",
            name="cancelled_at",
            field=models.DateTimeField(null=True, blank=True),
        ),
        
        # Обновляем статусы
        migrations.AlterField(
            model_name="deal",
            name="status",
            field=models.CharField(
                choices=[
                    ("draft", "Черновик"),
                    ("pending_payment", "Ожидает оплаты"),
                    ("in_progress", "В работе"),
                    ("revision_requested", "Нужна доработка"),
                    ("delivered", "Сдан на проверку"),
                    ("completed", "Завершен"),
                    ("cancelled", "Отменен"),
                    ("disputed", "Спор"),
                ],
                default="draft",
                max_length=30,
            ),
        ),
        migrations.AddIndex(
            model_name="deal",
            index=models.Index(fields=["status", "payment_completed"], name="deals_status_payment_idx"),
        ),
    ]
