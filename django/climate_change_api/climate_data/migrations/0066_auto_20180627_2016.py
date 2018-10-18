# -*- coding: utf-8 -*-
# Generated by Django 1.10.8 on 2018-06-27 20:16
from __future__ import unicode_literals

import climate_data.models
import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('climate_data', '0065_scenario_alias'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='city',
            options={'verbose_name_plural': 'cities'},
        ),
        migrations.AddField(
            model_name='city',
            name='datasets',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.CharField(choices=[('LOCA', 'LOCA'), ('NEX-GDDP', 'NEX-GDDP')], max_length=48), default=climate_data.models.get_datasets, size=2),
        ),
        migrations.AlterField(
            model_name='climatedataset',
            name='name',
            field=models.CharField(choices=[('LOCA', 'LOCA'), ('NEX-GDDP', 'NEX-GDDP')], max_length=48, unique=True),
        ),
    ]