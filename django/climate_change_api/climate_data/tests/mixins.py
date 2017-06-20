from django.contrib.gis.geos import Point

from climate_data.tests.factories import (CityFactory,
                                          ClimateModelFactory,
                                          RegionFactory,
                                          ScenarioFactory,
                                          ClimateDataFactory,
                                          ClimateDataSourceFactory,
                                          ClimateDataCellFactory,
                                          ClimateDataBaselineFactory,
                                          HistoricAverageClimateDataFactory)


class CityDataSetupMixin(object):
    """Creates a set of cities as mock data."""

    def setUp(self):
        super(CityDataSetupMixin, self).setUp()

        self.region = RegionFactory()

        self.city1 = CityFactory(name='Philadelphia', admin='us', region=self.region,
                                 population=10, geom=Point(10, 10))
        self.city2 = CityFactory(name='Washington DC', admin='us', region=self.region,
                                 population=20, geom=Point(20, 20))
        self.city3 = CityFactory(name='London', admin='uk',
                                 population=30, geom=Point(30, 30))


class ClimateDataSetupMixin(object):
    """Mixin to a TestCase class to provide some basic climate data to test against.

    Be sure to add this Mixin as an argument _before_ the TestCase class, since python uses
    the right-most class as the base class, and this is not a base class.

    e.g.
    ```
    class FooTestCase(ClimateDataSetupMixin, TestCase):
        pass
    ```

    Produces this data, all in one map cell:
    {
        'rcp45': {
            'model1': {
                '2000': [{'tasmax': 10, 'tasmin': 10, 'pr': 10}],
                '2001': [{'tasmax': 10, 'tasmin': 10, 'pr': 10}],
                '2002': [{'tasmax': 10, 'tasmin': 10, 'pr': 10}],
                '2003': [{'tasmax': 10, 'tasmin': 10, 'pr': 0}],
            },
            'model2': {
                '2000': [{'tasmax': 20, 'tasmin': 20, 'pr': 20}],
                '2001': [{'tasmax': 20, 'tasmin': 20, 'pr': 20}],
            },
        },
        'rcp85': {
            'model1': {
                '2000': [{'tasmax': 30, 'tasmin': 30, 'pr': 30}],
            },
            'model2': {
                '2000': [{'tasmax': 40, 'tasmin': 40, 'pr': 40}],
            },
        }
    }
    """

    def setUp(self):
        super(ClimateDataSetupMixin, self).setUp()

        self.rcp45 = ScenarioFactory(name='RCP45')
        self.rcp85 = ScenarioFactory(name='RCP85')

        self.model1 = ClimateModelFactory(name='CCSM4')
        self.model2 = ClimateModelFactory(name='CanESM2')

        self.mapcell = ClimateDataCellFactory(lat=15, lon=240)

        self.ds_s1_m1_2000 = ClimateDataSourceFactory(scenario=self.rcp45, model=self.model1,
                                                      year=2000)
        self.ds_s1_m1_2001 = ClimateDataSourceFactory(scenario=self.rcp45, model=self.model1,
                                                      year=2001)
        self.ds_s1_m1_2002 = ClimateDataSourceFactory(scenario=self.rcp45, model=self.model1,
                                                      year=2002)
        self.ds_s1_m1_2003 = ClimateDataSourceFactory(scenario=self.rcp45, model=self.model1,
                                                      year=2003)

        self.ds_s1_m2_2000 = ClimateDataSourceFactory(scenario=self.rcp45, model=self.model2,
                                                      year=2000)
        self.ds_s1_m2_2001 = ClimateDataSourceFactory(scenario=self.rcp45, model=self.model2,
                                                      year=2001)

        self.ds_s2_m1_2000 = ClimateDataSourceFactory(scenario=self.rcp85, model=self.model1,
                                                      year=2000)

        self.ds_s2_m2_2000 = ClimateDataSourceFactory(scenario=self.rcp85, model=self.model2,
                                                      year=2000)

        ClimateDataFactory(map_cell=self.mapcell, data_source=self.ds_s1_m1_2000, day_of_year=1,
                           tasmax=10, tasmin=10, pr=10)

        ClimateDataFactory(map_cell=self.mapcell, data_source=self.ds_s1_m2_2000, day_of_year=1,
                           tasmax=20, tasmin=20, pr=20)

        ClimateDataFactory(map_cell=self.mapcell, data_source=self.ds_s1_m1_2001, day_of_year=1,
                           tasmax=10, tasmin=10, pr=10)

        ClimateDataFactory(map_cell=self.mapcell, data_source=self.ds_s1_m2_2001, day_of_year=1,
                           tasmax=20, tasmin=20, pr=20)

        ClimateDataFactory(map_cell=self.mapcell, data_source=self.ds_s1_m1_2002, day_of_year=1,
                           tasmax=10, tasmin=10, pr=10)

        ClimateDataFactory(map_cell=self.mapcell, data_source=self.ds_s1_m1_2003, day_of_year=1,
                           tasmax=10, tasmin=10, pr=0)

        ClimateDataFactory(map_cell=self.mapcell, data_source=self.ds_s2_m1_2000, day_of_year=1,
                           tasmax=30, tasmin=30, pr=30)

        ClimateDataFactory(map_cell=self.mapcell, data_source=self.ds_s2_m2_2000, day_of_year=1,
                           tasmax=40, tasmin=40, pr=40)

        ClimateDataBaselineFactory(map_cell=self.mapcell, percentile=99,
                                   tasmax=20, tasmin=20, pr=20)

        ClimateDataBaselineFactory(map_cell=self.mapcell, percentile=1,
                                   tasmax=10, tasmin=15, pr=15)

        HistoricAverageClimateDataFactory(map_cell=self.mapcell, day_of_year=1,
                                          tasmax=0, tasmin=0, pr=0)

        self.city1 = CityFactory(name='city1', admin='city1', map_cell=self.mapcell)
        self.city2 = CityFactory(name='city2', admin='city2')
