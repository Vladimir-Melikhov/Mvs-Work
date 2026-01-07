from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("services", "0002_add_last_message_id"),
    ]

    operations = [
        migrations.AddField(
            model_name='deal',
            name='paid_at',
            field=models.DateTimeField(null=True, blank=True, help_text='Дата оплаты'),
        ),
    ]