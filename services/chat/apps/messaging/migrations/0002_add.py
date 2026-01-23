# Generated migration for adding external_url field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('messaging', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='messageattachment',
            name='file',
            field=models.FileField(
                blank=True,
                help_text='Файл-вложение (до 20MB)',
                max_length=500,
                null=True,
                upload_to='message_attachments/temp/'
            ),
        ),
        migrations.AddField(
            model_name='messageattachment',
            name='external_url',
            field=models.URLField(
                blank=True,
                help_text='URL файла на внешнем сервисе (например, market service)',
                max_length=1000
            ),
        ),
    ]
