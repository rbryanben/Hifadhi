# Generated by Django 4.0.3 on 2022-04-30 07:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Shared', '0003_storedfile_public'),
    ]

    operations = [
        migrations.AddField(
            model_name='cachedfile',
            name='public',
            field=models.BooleanField(default=True),
        ),
    ]
