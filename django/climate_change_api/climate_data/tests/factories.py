from datetime import datetime

from django.contrib.gis.geos import Point, Polygon

from factory.django import DjangoModelFactory
import factory

from climate_data.models import (City,
                                 ClimateDataBaseline,
                                 ClimateDataCell,
                                 ClimateDataSource,
                                 ClimateDataset,
                                 ClimateDataYear,
                                 ClimateModel,
                                 HistoricAverageClimateDataYear,
                                 HistoricDateRange,
                                 Region,
                                 Scenario)


class RegionFactory(DjangoModelFactory):

    level1 = 8
    level2 = 5
    level1_description = "EASTERN TEMPERATE FORESTS"
    level2_description = "MISSISSIPPI ALLUVIAL AND SOUTHEAST USA COASTAL PLAINS"
    geom = Polygon([(0, 0), (0, 1), (1, 1), (1, 0), (0, 0)])

    class Meta:
        model = Region
        django_get_or_create = ('level1', 'level2',)


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


class ClimateDatasetFactory(DjangoModelFactory):
    name = 'NEX-GDDP'
    label = ''
    description = ''
    url = ''

    class Meta:
        model = ClimateDataset
        django_get_or_create = ('name',)


class ClimateDataCellFactory(DjangoModelFactory):

    lat = 0
    lon = 0
    dataset = ClimateDatasetFactory()

    class Meta:
        model = ClimateDataCell
        django_get_or_create = ('lat', 'lon', 'dataset')


class HistoricDateRangeFactory(DjangoModelFactory):

    start_year = 1951
    end_year = 1980

    class Meta:
        model = HistoricDateRange
        django_get_or_create = ('start_year', 'end_year')


class ClimateDataYearFactory(DjangoModelFactory):

    map_cell = ClimateDataCellFactory()
    data_source = ClimateDataSourceFactory()
    tasmin = [273]
    tasmax = [293]
    pr = [0.0001]

    class Meta:
        model = ClimateDataYear
        django_get_or_create = ('map_cell', 'data_source',)


class ClimateDataBaselineFactory(DjangoModelFactory):

    map_cell = ClimateDataCellFactory()
    percentile = 99
    tasmin = 272
    tasmax = 292
    pr = 0.00005
    historic_range = HistoricDateRangeFactory()

    class Meta:
        model = ClimateDataBaseline
        django_get_or_create = ('map_cell', 'percentile', 'historic_range')


class HistoricAverageClimateDataYearFactory(DjangoModelFactory):

    map_cell = ClimateDataCellFactory()
    tasmin = [0]
    tasmax = [0]
    pr = [0]
    historic_range = HistoricDateRangeFactory()

    class Meta:
        model = HistoricAverageClimateDataYear
        django_get_or_create = ('map_cell', 'historic_range')
