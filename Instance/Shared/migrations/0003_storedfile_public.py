# Generated by Django 4.0.3 on 2022-04-20 10:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Shared', '0002_cachedfile'),
    ]

    operations = [
        migrations.AddField(
            model_name='storedfile',
            name='public',
            field=models.BooleanField(default=False),
        ),
    ]
