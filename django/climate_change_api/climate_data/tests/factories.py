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
        django_get_or_create = ('city', 'climate_model', 'year', 'day_of_year',)


def generate_climate_data():
    """ Generate some test data to populate db with

    This takes about 1 second to run, so its best to call this only in the test_*() method
    you will be directly using it in, rather than in setUp()

    """
    climate_data = ClimateDataFactory()
    scenario = ScenarioFactory()
    for model in (ClimateModelFactory(), ClimateModelFactory(name='ukmet'),):
        for year in range(climate_data.year + 1, climate_data.year + 4):
            for day in range(1, 50):
                tasmin = climate_data.tasmin + day / 10
                tasmax = climate_data.tasmax + day / 10
                pr = climate_data.pr + day / 500000.0
                ClimateDataFactory(climate_model=model, scenario=scenario, year=year,
                                   day_of_year=day, tasmin=tasmin, tasmax=tasmax, pr=pr)
