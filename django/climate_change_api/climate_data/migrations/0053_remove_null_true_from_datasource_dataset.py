# -*- coding: utf-8 -*-
# Generated by Django 1.10.7 on 2017-08-22 20:31
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('climate_data', '0052_default_source_dataset'),
    ]

    operations = [
        migrations.AlterField(
            model_name='climatedatasource',
            name='dataset',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='climate_data.ClimateDataset'),
        ),
    ]
