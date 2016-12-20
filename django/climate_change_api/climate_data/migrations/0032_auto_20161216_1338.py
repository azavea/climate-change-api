# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2016-12-16 13:38
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('climate_data', '0031_auto_20161208_1845'),
    ]

    operations = [
        migrations.RenameField(
            model_name='city',
            old_name='boundary',
            new_name='boundary_temp',
        ),
        migrations.AddField(
            model_name='cityboundary',
            name='city_temp',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='boundary', to='climate_data.City'),
        ),
    ]
