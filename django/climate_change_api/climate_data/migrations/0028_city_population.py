# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2016-11-08 19:20
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('climate_data', '0027_auto_20161020_1757'),
    ]

    operations = [
        migrations.AddField(
            model_name='city',
            name='population',
            field=models.IntegerField(null=True),
        ),
    ]