# Generated by Django 5.0.6 on 2024-09-04 13:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('loans', '0007_alter_loanhist_trx_date'),
    ]

    operations = [
        migrations.AlterField(
            model_name='loanhist',
            name='trx_date',
            field=models.DateField(),
        ),
    ]
