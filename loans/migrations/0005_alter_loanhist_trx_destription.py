# Generated by Django 5.0.6 on 2024-09-03 08:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('loans', '0004_loanhist_trx_destription'),
    ]

    operations = [
        migrations.AlterField(
            model_name='loanhist',
            name='trx_destription',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
    ]
