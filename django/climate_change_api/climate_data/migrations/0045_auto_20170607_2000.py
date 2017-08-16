# -*- coding: utf-8 -*-
# Generated by Django 1.10.7 on 2017-06-07 20:00
from __future__ import unicode_literals

import climate_data.models
import django.contrib.postgres.fields
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('climate_data', '0044_auto_20170606_1947'),
    ]

    operations = [
        migrations.CreateModel(
            name='ClimateDataYear',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('tasmin', django.contrib.postgres.fields.ArrayField(base_field=models.FloatField(), help_text='Daily Minimum Near-Surface Air Temperature, Kelvin', size=None)),
                ('tasmax', django.contrib.postgres.fields.ArrayField(base_field=models.FloatField(), help_text='Daily Maximum Near-Surface Air Temperature, Kelvin', size=None)),
                ('pr', django.contrib.postgres.fields.ArrayField(base_field=models.FloatField(), help_text='Precipitation (mean of the daily precipitation rate), kg m-2 s-1', size=None)),
                ('data_source', climate_data.models.TinyForeignKey(on_delete=django.db.models.deletion.CASCADE, to='climate_data.ClimateDataSource')),
                ('map_cell', climate_data.models.TinyForeignKey(on_delete=django.db.models.deletion.CASCADE, to='climate_data.ClimateDataCell')),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='climatedatayear',
            unique_together=set([('map_cell', 'data_source')]),
        ),
        migrations.AlterIndexTogether(
            name='climatedatayear',
            index_together=set([('map_cell', 'data_source')]),
        ),
    ]
