# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2016-11-21 17:53
from __future__ import unicode_literals

import django.contrib.gis.db.models.fields
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('climate_data', '0028_city_population'),
    ]

    operations = [
        migrations.CreateModel(
            name='Region',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('geom', django.contrib.gis.db.models.fields.GeometryField(srid=4326)),
                ('level1', models.IntegerField()),
                ('level2', models.IntegerField()),
                ('level1_description', models.CharField(max_length=64)),
                ('level2_description', models.CharField(max_length=64)),
            ],
        ),
        migrations.AddField(
            model_name='city',
            name='region',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='climate_data.Region'),
        ),
    ]