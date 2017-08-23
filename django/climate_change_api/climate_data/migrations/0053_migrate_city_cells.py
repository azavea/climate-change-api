# -*- coding: utf-8 -*-
# Generated by Django 1.10.7 on 2017-08-22 21:09
from __future__ import unicode_literals
import itertools

from django.db import migrations


def chunk_sequence(it, size):
    chunk = list(itertools.islice(it, size))
    while len(chunk) > 0:
        yield chunk
        chunk = list(itertools.islice(it, size))


class Migration(migrations.Migration):

    def migrate_city_cells_many_to_many(apps, schema_editor):
        City = apps.get_model('climate_data', 'City')
        ClimateDataCityCell = apps.get_model('climate_data', 'ClimateDataCityCell')
        ClimateDataset = apps.get_model('climate_data', 'ClimateDataset')

        gddp = ClimateDataset.objects.get(name='NEX-GDDP')

        city_data = City.objects.all().values('id', 'map_cell_id')

        # Create a default many-to-many relationship for GDDP for all Cities and their current
        # one-to-many map cell foreign key
        city_cell_objects = (ClimateDataCityCell(
            city_id=row['id'],
            cell_id=row['map_cell_id'],
            dataset=gddp
        ) for row in city_data)

        city_cell_chunks = chunk_sequence(city_cell_objects, 200)

        for chunk in city_cell_chunks:
            ClimateDataCityCell.objects.bulk_create(chunk)

    dependencies = [
        ('climate_data', '0052_auto_20170822_2036'),
    ]

    operations = [
        migrations.RunPython(migrate_city_cells_many_to_many, migrations.RunPython.noop)
    ]
