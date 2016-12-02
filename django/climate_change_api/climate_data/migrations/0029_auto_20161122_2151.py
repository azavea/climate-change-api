# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2016-11-22 21:51
from __future__ import unicode_literals

import climate_data.models
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('climate_data', '0028_city_population'),
    ]

    operations = [
        migrations.AddField(
            model_name='climatedatabaseline',
            name='percentile',
            field=models.IntegerField(default=99),
            preserve_default=False,
        ),
        migrations.RenameField(
            model_name='climatedatabaseline',
            old_name='precip_99p',
            new_name='pr'
        ),
        migrations.AlterField(
            model_name='climatedatabaseline',
            name='pr',
            field=models.FloatField(help_text='Historic greatest daily precipitation for this percentile from 1961-1990', null=True),
        ),
        migrations.AddField(
            model_name='climatedatabaseline',
            name='tasmax',
            field=models.FloatField(help_text='Historic greatest daily maximum temperature for this percentile from 1961-1990', null=True),
        ),
        migrations.AddField(
            model_name='climatedatabaseline',
            name='tasmin',
            field=models.FloatField(help_text='Historic least daily minimum temperature for this percentile from 1961-1990', null=True),
        ),
        migrations.AlterField(
            model_name='climatedatabaseline',
            name='map_cell',
            field=climate_data.models.TinyForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='baseline', to='climate_data.ClimateDataCell'),
        ),
        migrations.AlterUniqueTogether(
            name='climatedatabaseline',
            unique_together=set([('map_cell', 'percentile')]),
        ),

    ]
