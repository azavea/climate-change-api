# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2016-07-15 16:53
from __future__ import unicode_literals

import climate_data.models
from django.db import migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('climate_data', '0013_climatemodel_base_time'),
    ]

    operations = [
        migrations.AlterField(
            model_name='climatedata',
            name='city',
            field=climate_data.models.TinyForeignKey(on_delete=django.db.models.deletion.CASCADE, to='climate_data.City'),
        ),
        migrations.AlterField(
            model_name='climatedata',
            name='climate_model',
            field=climate_data.models.TinyForeignKey(on_delete=django.db.models.deletion.CASCADE, to='climate_data.ClimateModel'),
        ),
        migrations.AlterField(
            model_name='climatedata',
            name='scenario',
            field=climate_data.models.TinyForeignKey(on_delete=django.db.models.deletion.CASCADE, to='climate_data.Scenario'),
        ),
    ]
