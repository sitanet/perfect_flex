# Generated by Django 5.0.6 on 2024-08-15 22:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('transactions', '0008_interestrate_ses_date'),
    ]

    operations = [
        migrations.AlterField(
            model_name='memtrans',
            name='app_date',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
