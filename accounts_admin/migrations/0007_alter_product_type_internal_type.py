# Generated by Django 5.0.1 on 2024-01-19 10:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts_admin', '0006_account_product_type'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product_type',
            name='internal_type',
            field=models.CharField(blank=True, max_length=6, null=True),
        ),
    ]
