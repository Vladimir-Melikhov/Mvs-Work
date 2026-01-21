# Generated manually to add missing content_type field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('messaging', '0002_messageattachment'),
    ]

    operations = [
        migrations.AddField(
            model_name='messageattachment',
            name='content_type',
            field=models.CharField(blank=True, max_length=100),
        ),
    ]