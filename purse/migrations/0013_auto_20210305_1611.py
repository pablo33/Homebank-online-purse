# Generated by Django 3.0.11 on 2021-03-05 15:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('purse', '0012_auto_20210305_1610'),
    ]

    operations = [
        migrations.AlterField(
            model_name='expense',
            name='date',
            field=models.DateField(null=True, verbose_name='Date'),
        ),
    ]
