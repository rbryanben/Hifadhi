# Generated by Django 4.0.3 on 2022-07-07 10:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Shared', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='cachedfile',
            name='reads',
            field=models.BigIntegerField(default=1),
        ),
    ]
