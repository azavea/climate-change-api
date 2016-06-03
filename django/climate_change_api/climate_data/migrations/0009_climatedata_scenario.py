# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2016-06-03 12:51
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('climate_data', '0008_scenario'),
    ]

    operations = [
        migrations.AddField(
            model_name='climatedata',
            name='scenario',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='climate_data.Scenario'),
        ),
    ]
