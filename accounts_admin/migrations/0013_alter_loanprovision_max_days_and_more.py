# Generated by Django 5.0.6 on 2024-09-11 14:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts_admin', '0012_loanprovision_delete_loan_provisions'),
    ]

    operations = [
        migrations.AlterField(
            model_name='loanprovision',
            name='max_days',
            field=models.BigIntegerField(help_text='Maximum days of arrears'),
        ),
        migrations.AlterField(
            model_name='loanprovision',
            name='rate',
            field=models.DecimalField(decimal_places=2, max_digits=100),
        ),
    ]
