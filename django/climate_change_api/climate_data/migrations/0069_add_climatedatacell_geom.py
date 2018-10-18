# -*- coding: utf-8 -*-
# Generated by Django 1.10.8 on 2018-10-18 20:29
from __future__ import unicode_literals

import django.contrib.gis.db.models.fields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('climate_data', '0068_set_climatedatacell_cell_sizes'),
    ]

    operations = [
        migrations.AddField(
            model_name='climatedatacell',
            name='geom',
            field=django.contrib.gis.db.models.fields.PointField(blank=True, null=True, srid=4326),
        ),
    ]
