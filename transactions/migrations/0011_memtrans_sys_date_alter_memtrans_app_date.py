# Generated by Django 5.0.6 on 2024-08-16 05:38

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('transactions', '0010_alter_memtrans_app_date'),
    ]

    operations = [
        migrations.AddField(
            model_name='memtrans',
            name='sys_date',
            field=models.DateTimeField(blank=True, default=django.utils.timezone.now, null=True),
        ),
        migrations.AlterField(
            model_name='memtrans',
            name='app_date',
            field=models.DateField(blank=True, null=True),
        ),
    ]
