# Generated by Django 4.2.6 on 2023-11-17 14:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts_admin', '0002_account_officer_user'),
    ]

    operations = [
        migrations.CreateModel(
            name='Business_Sector',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sector_name', models.CharField(max_length=30, unique=True)),
            ],
        ),
    ]