from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('messaging', '0002_add_display_mode'),
    ]

    operations = [
        migrations.AddField(
            model_name='room',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.CreateModel(
            name='ReadReceipt',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('user_id', models.UUIDField(db_index=True)),
                ('last_read_at', models.DateTimeField(auto_now=True)),
                ('last_read_message', models.ForeignKey(blank=True, help_text='Последнее прочитанное сообщение', null=True, on_delete=django.db.models.deletion.SET_NULL, to='messaging.message')),
                ('room', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='read_receipts', to='messaging.room')),
            ],
            options={
                'db_table': 'read_receipts',
                'unique_together': {('room', 'user_id')},
            },
        ),
        migrations.AddIndex(
            model_name='room',
            index=models.Index(fields=['-updated_at'], name='rooms_updated_idx'),
        ),
        migrations.AddIndex(
            model_name='message',
            index=models.Index(fields=['room', '-created_at'], name='messages_room_created_idx'),
        ),
        migrations.AddIndex(
            model_name='readreceipt',
            index=models.Index(fields=['room', 'user_id'], name='read_receipts_room_user_idx'),
        ),
    ]
