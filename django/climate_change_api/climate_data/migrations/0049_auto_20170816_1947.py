# -*- coding: utf-8 -*-
# Generated by Django 1.10.7 on 2017-08-16 19:47
from __future__ import unicode_literals

import climate_data.models
from django.db import migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('climate_data', '0048_climatedataset_load'),
    ]

    operations = [
        migrations.AddField(
            model_name='climatedatacell',
            name='dataset',
            field=climate_data.models.TinyForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='map_cells', to='climate_data.ClimateDataset'),
        ),
    ]
