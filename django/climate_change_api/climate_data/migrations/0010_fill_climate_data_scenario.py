# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2016-06-03 12:52
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations


def fill_climate_data_scenario_forwards(apps, schema_editor):
    Scenario = apps.get_model("climate_data", "Scenario")
    ClimateData = apps.get_model("climate_data", "ClimateData")

    # Fill with a placeholder scenario, so that we don't disrupt existing data
    # You are responsible for attaching the correct scenario to existing data,
    # because you know best where it came from.
    scenario, created = Scenario.objects.get_or_create(name=settings.PLACEHOLDER_SCENARIO_NAME)
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
