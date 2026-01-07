# services/market/apps/services/migrations/0005_remove_unique_chat_room.py

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("services", "0003_improved_deal_model"),
    ]

    operations = [
        # Сначала удаляем старый индекс если он есть
        migrations.RunSQL(
            sql="DROP INDEX IF EXISTS deals_chat_room_id_f25ee42a;",
            reverse_sql="CREATE INDEX deals_chat_room_id_f25ee42a ON deals (chat_room_id);"
        ),
        # Удаляем уникальный constraint если он есть
        migrations.RunSQL(
            sql="ALTER TABLE deals DROP CONSTRAINT IF EXISTS services_deal_chat_room_id_key;",
            reverse_sql="ALTER TABLE deals ADD CONSTRAINT services_deal_chat_room_id_key UNIQUE (chat_room_id);"
        ),
        # Создаём обычный индекс без unique
        migrations.RunSQL(
            sql="CREATE INDEX IF NOT EXISTS deals_chat_room_id_idx ON deals (chat_room_id);",
            reverse_sql="DROP INDEX IF EXISTS deals_chat_room_id_idx;"
        ),
    ]