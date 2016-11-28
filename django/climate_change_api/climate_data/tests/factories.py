from datetime import datetime

from django.contrib.gis.geos import Point

from factory.django import DjangoModelFactory
import factory

from climate_data.models import (ClimateModel, City, ClimateData, ClimateDataBaseline,
                                 ClimateDataSource, Scenario, ClimateDataCell)


class CityFactory(DjangoModelFactory):

    name = 'Null Island'
    admin = 'atl_ocean'
    geom = Point(0, 0, srid=4326)

    class Meta:
        model = City
        django_get_or_create = ('name', 'admin',)

    @factory.post_generation
    def map_cells(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for map_cell in extracted:
                self.map_cells.add(map_cell)


class ScenarioFactory(DjangoModelFactory):
    name = 'RCP45'
    label = None
    description = None

    class Meta:
        model = Scenario
        django_get_or_create = ('name',)


class ClimateModelFactory(DjangoModelFactory):

    name = 'CCSM4'
    label = 'CCSM4'
    base_time = datetime(2000, 1, 1)

    class Meta:
        model = ClimateModel
        django_get_or_create = ('name',)


class ClimateDataSourceFactory(DjangoModelFactory):

    model = ClimateModelFactory()
    scenario = ScenarioFactory()
    year = 2000

    class Meta:
        model = ClimateDataSource
        django_get_or_create = ('model', 'scenario', 'year',)


class ClimateDataCellFactory(DjangoModelFactory):

    lat = 0
    lon = 0

    class Meta:
        model = ClimateDataCell
        django_get_or_create = ('lat', 'lon',)


class ClimateDataFactory(DjangoModelFactory):

    map_cell = ClimateDataCellFactory()
    data_source = ClimateDataSourceFactory()
    day_of_year = 1
    tasmin = 273
    tasmax = 293
    pr = 0.0001

    class Meta:
        model = ClimateData
        django_get_or_create = ('map_cell', 'data_source', 'day_of_year',)


class ClimateDataBaselineFactory(DjangoModelFactory):

    map_cell = ClimateDataCellFactory()
    percentile = 99
    tasmin = 272
    tasmax = 292
    pr = 0.00005

    class Meta:
        model = ClimateDataBaseline
        django_get_or_create = ('map_cell', 'percentile',)
