from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("services", "0003_improved_deal_model"),
    ]

    operations = [
        migrations.AlterField(
            model_name="deal",
            name="chat_room_id",
            field=models.UUIDField(db_index=True),
        ),
    ]
