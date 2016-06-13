from django.contrib.gis.geos import Point

from factory.django import DjangoModelFactory

from climate_data.models import ClimateModel, City, ClimateData, Scenario


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

    class Meta:
        model = ClimateModel
        django_get_or_create = ('name',)


class ClimateDataFactory(DjangoModelFactory):

    city = CityFactory()
    climate_model = ClimateModelFactory()
    scenario = ScenarioFactory()
    year = 2000
    day_of_year = 1
    tasmin = 273
    tasmax = 293
    pr = 0.0001

    class Meta:
        model = ClimateData
        django_get_or_create = ('city', 'scenario', 'climate_model', 'year', 'day_of_year',)
