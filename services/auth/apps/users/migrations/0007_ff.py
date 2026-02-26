from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        # Укажите вашу последнюю миграцию, например:
        ('users', '0006_emailverification_new_email_and_more'),
    ]

    operations = [
        # Добавляем is_staff
        migrations.AddField(
            model_name='user',
            name='is_staff',
            field=models.BooleanField(
                default=False,
                help_text='Доступ к административной панели'
            ),
        ),
        # Добавляем is_superuser
        migrations.AddField(
            model_name='user',
            name='is_superuser',
            field=models.BooleanField(
                default=False,
                help_text='Все права без ограничений'
            ),
        ),
        # Добавляем роль admin в choices
        migrations.AlterField(
            model_name='user',
            name='role',
            field=models.CharField(
                max_length=10,
                choices=[
                    ('client', 'Client'),
                    ('worker', 'Worker'),
                    ('admin', 'Admin'),
                ],
                default='client'
            ),
        ),
        # Таблицы для PermissionsMixin (groups и user_permissions)
        migrations.AddField(
            model_name='user',
            name='groups',
            field=models.ManyToManyField(
                blank=True,
                help_text='The groups this user belongs to.',
                related_name='user_set',
                related_query_name='user',
                to='auth.Group',
                verbose_name='groups',
            ),
        ),
        migrations.AddField(
            model_name='user',
            name='user_permissions',
            field=models.ManyToManyField(
                blank=True,
                help_text='Specific permissions for this user.',
                related_name='user_set',
                related_query_name='user',
                to='auth.Permission',
                verbose_name='user permissions',
            ),
        ),
    ]
