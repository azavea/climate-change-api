# -*- coding: utf-8 -*-
# Generated by Django 1.9.12 on 2017-04-14 18:06
from __future__ import unicode_literals

import climate_data.models
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('climate_data', '0040_climatedatasource_import_completed'),
    ]

    operations = [
        migrations.AlterField(
            model_name='climatedata',
            name='id',
            field=climate_data.models.BigAutoField(primary_key=True, serialize=False),
        ),
    ]
