# Generated by Django 5.0.6 on 2024-08-09 19:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('company', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='company',
            name='branch_code',
            field=models.PositiveIntegerField(),
        ),
    ]
