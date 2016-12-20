# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2016-12-16 13:42
from __future__ import unicode_literals

from django.db import migrations


def swap_city_cityboundary(apps, schema_editor):
    City = apps.get_model('climate_data', 'City')
    CityBoundary = apps.get_model('climate_data', 'CityBoundary')
    for city in City.objects.all():
        boundary = city.boundary_temp
        if boundary is not None:
            boundary.city_temp = city
            boundary.save()


def reverse_swap_city_cityboundary(apps, schema_editor):
    City = apps.get_model('climate_data', 'City')
    CityBoundary = apps.get_model('climate_data', 'CityBoundary')
    for boundary in CityBoundary.objects.all():
        city = boundary.city_temp
        if city is not None:
            city.boundary_temp = boundary
            city.save()


class Migration(migrations.Migration):

    dependencies = [
        ('climate_data', '0032_auto_20161216_1338'),
    ]

    operations = [
        migrations.RunPython(swap_city_cityboundary, reverse_swap_city_cityboundary)
    ]
