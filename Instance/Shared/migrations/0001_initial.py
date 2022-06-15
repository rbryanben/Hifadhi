# Generated by Django 4.0.3 on 2022-06-15 11:23

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='cachedFile',
            fields=[
                ('fileQueryName', models.CharField(max_length=512, primary_key=True, serialize=False)),
                ('cached', models.DateTimeField(auto_now=True)),
                ('public', models.BooleanField(default=True)),
                ('size', models.BigIntegerField(default=0)),
                ('priority', models.IntegerField(default=0)),
            ],
        ),
        migrations.CreateModel(
            name='registeredInstance',
            fields=[
                ('ipv4', models.CharField(max_length=15)),
                ('total_memory', models.BigIntegerField(default=0)),
                ('used_memory', models.BigIntegerField(default=0)),
                ('stored_files_size', models.BigIntegerField(default=0)),
                ('cached_files_size', models.BigIntegerField(default=0)),
                ('instance_name', models.CharField(max_length=512, primary_key=True, serialize=False)),
                ('stored_files_count', models.IntegerField(default=0)),
                ('cached_files_count', models.IntegerField(default=0)),
                ('uptime', models.BigIntegerField(default=0)),
                ('last_health_check', models.DateTimeField(auto_now=True)),
                ('healthy', models.BooleanField(default=True)),
            ],
        ),
        migrations.CreateModel(
            name='storedFile',
            fields=[
                ('filename', models.CharField(max_length=512, primary_key=True, serialize=False)),
                ('stored', models.DateTimeField(auto_now=True)),
                ('public', models.BooleanField(default=False)),
                ('size', models.BigIntegerField(default=0)),
            ],
        ),
        migrations.CreateModel(
            name='presignedURL',
            fields=[
                ('signature', models.CharField(max_length=256, primary_key=True, serialize=False)),
                ('expires', models.DateTimeField()),
                ('created', models.DateTimeField(auto_now=True)),
                ('file', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Shared.storedfile')),
            ],
        ),
        migrations.CreateModel(
            name='ipv4Access',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ipv4', models.CharField(max_length=25)),
                ('expires', models.DateTimeField()),
                ('created', models.DateTimeField(auto_now=True)),
                ('file', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Shared.storedfile')),
            ],
        ),
    ]
