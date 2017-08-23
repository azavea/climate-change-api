# -*- coding: utf-8 -*-
# Generated by Django 1.10.7 on 2017-08-22 20:36
from __future__ import unicode_literals

import climate_data.models
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('climate_data', '0051_auto_20170822_2031'),
    ]

    operations = [
        migrations.CreateModel(
            name='ClimateDataCityCell',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cell', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='city_set', to='climate_data.ClimateDataCell')),
                ('city', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='cell_set', to='climate_data.City')),
                ('dataset', climate_data.models.TinyForeignKey(on_delete=django.db.models.deletion.CASCADE, to='climate_data.ClimateDataset')),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='climatedatacitycell',
            unique_together=set([('city', 'dataset')]),
        ),
    ]
