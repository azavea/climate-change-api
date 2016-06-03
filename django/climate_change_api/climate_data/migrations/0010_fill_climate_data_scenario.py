# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2016-06-03 12:52
from __future__ import unicode_literals

from django.db import migrations


def fill_climate_data_scenario_forwards(apps, schema_editor):
    Scenario = apps.get_model("climate_data", "Scenario")
    ClimateData = apps.get_model("climate_data", "ClimateData")

    # This migration existed before we had real data in the repo, so
    # to keep things simple we just update each data point with a
    # null scenario to use a default valid Scenario
    scenario, created = Scenario.objects.get_or_create(name='RCP45')
    for data in ClimateData.objects.filter(scenario__isnull=True):
        data.scenario = scenario
        data.save()


def fill_climate_data_scenario_backwards(apps, schema_editor):
    """ Do nothing, we're just setting the scenario field to allow NULL """
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('climate_data', '0009_climatedata_scenario'),
    ]

    operations = [
        migrations.RunPython(fill_climate_data_scenario_forwards,
                             fill_climate_data_scenario_backwards)
    ]
