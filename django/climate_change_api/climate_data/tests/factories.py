from datetime import datetime

from django.contrib.gis.geos import Point

from factory.django import DjangoModelFactory

from climate_data.models import ClimateModel, City, ClimateData, ClimateDataSource, Scenario


class CityFactory(DjangoModelFactory):

    name = 'Null Island'
    admin = 'atl_ocean'
    geom = Point(0, 0, srid=4326)

    class Meta:
        model = City
        django_get_or_create = ('name', 'admin',)


class ScenarioFactory(DjangoModelFactory):
    name = 'RCP45'
    description = None

    class Meta:
        model = Scenario
        django_get_or_create = ('name',)


class ClimateModelFactory(DjangoModelFactory):

    name = 'ncar'
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


class ClimateDataFactory(DjangoModelFactory):

    city = CityFactory()
    data_source = ClimateDataSourceFactory()
    day_of_year = 1
    tasmin = 273
    tasmax = 293
    pr = 0.0001

    class Meta:
        model = ClimateData
        django_get_or_create = ('city', 'data_source', 'day_of_year',)
