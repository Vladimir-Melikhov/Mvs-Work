from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('messaging', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='messageattachment',
            name='display_mode',
            field=models.CharField(
                choices=[
                    ('inline', 'Показать как изображение'),
                    ('attachment', 'Показать как файл для скачивания'),
                ],
                default='inline',
                help_text='Как отображать файл в чате',
                max_length=20,
            ),
        ),
    ]
