# Generated by Django 3.0.5 on 2021-02-28 10:20

import datetime
from django.db import migrations, models
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('purse', '0010_auto_20210227_1039'),
    ]

    operations = [
        migrations.AddField(
            model_name='visitcounter',
            name='app',
            field=models.CharField(blank=True, max_length=50, null=True, verbose_name='App'),
        ),
        migrations.AlterField(
            model_name='expense',
            name='date',
            field=models.DateField(default=datetime.datetime(2021, 2, 28, 10, 20, 38, 962200, tzinfo=utc), verbose_name='Date'),
        ),
    ]
