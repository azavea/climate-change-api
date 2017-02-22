# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2017-02-22 20:04
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user_management', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='climateuser',
            name='burst_rate',
            field=models.CharField(default=b'20/min', max_length=10, verbose_name='burst rate'),
        ),
        migrations.AddField(
            model_name='climateuser',
            name='sustained_rate',
            field=models.CharField(default=b'5000/day', max_length=10, verbose_name='sustained rate'),
        ),
    ]
