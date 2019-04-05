# -*- coding: utf-8 -*-
# Generated by Django 1.10.8 on 2018-12-10 20:45
from __future__ import unicode_literals

from django.db import migrations


def set_cell_geography(apps, schema_editor):
    ClimateDataCell = apps.get_model('climate_data', 'ClimateDataCell')
    for obj in ClimateDataCell.objects.all():
        obj.geog = obj.geom
        obj.save()


class Migration(migrations.Migration):

    dependencies = [
        ('climate_data', '0072_climatedatacell_geog'),
    ]

    operations = [
        migrations.RunPython(set_cell_geography, reverse_code=migrations.RunPython.noop),
    ]