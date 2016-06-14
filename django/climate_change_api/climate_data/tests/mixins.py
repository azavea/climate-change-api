from climate_data.tests.factories import (CityFactory,
                                          ClimateModelFactory,
                                          ScenarioFactory,
                                          ClimateDataFactory)
from django.contrib.gis.geos import Point


class CityDataSetupMixin(object):
    """ Creates a set of cities as mock data """
    def setUp(self):
        super(CityDataSetupMixin, self).setUp()

        self.city1 = CityFactory(name='Philadelphia', admin='us', geom=Point(10, 10))
        self.city2 = CityFactory(name='Washington DC', admin='us', geom=Point(20, 20))
        self.city3 = CityFactory(name='London', admin='uk', geom=Point(30, 30))


class ClimateDataSetupMixin(object):
    """ Mixin to a TestCase class to provide some basic climate data to test against

    Be sure to add this Mixin as an argument _before_ the TestCase class, since python uses
    the right-most class as the base class, and this is not a base class.

    e.g.
    ```
    class FooTestCase(ClimateDataSetupMixin, TestCase):
        pass
    ```

    """
    def setUp(self):
        super(ClimateDataSetupMixin, self).setUp()

        self.city1 = CityFactory(name='city1', admin='city1')
        self.city2 = CityFactory(name='city2', admin='city2')

        self.rcp45 = ScenarioFactory(name='RCP45')
        self.rcp85 = ScenarioFactory(name='RCP85')

        self.model1 = ClimateModelFactory(name='model1')
        self.model2 = ClimateModelFactory(name='model2')

        ClimateDataFactory(city=self.city1, scenario=self.rcp45, climate_model=self.model1,
                           year=2000, day_of_year=1,
                           tasmax=10, tasmin=10, pr=10)

        ClimateDataFactory(city=self.city1, scenario=self.rcp45, climate_model=self.model2,
                           year=2000, day_of_year=1,
                           tasmax=20, tasmin=20, pr=20)

        ClimateDataFactory(city=self.city1, scenario=self.rcp45, climate_model=self.model1,
                           year=2001, day_of_year=1,
                           tasmax=10, tasmin=10, pr=10)

        ClimateDataFactory(city=self.city1, scenario=self.rcp45, climate_model=self.model2,
                           year=2001, day_of_year=1,
                           tasmax=20, tasmin=20, pr=20)

        ClimateDataFactory(city=self.city1, scenario=self.rcp45, climate_model=self.model1,
                           year=2002, day_of_year=1,
                           tasmax=10, tasmin=10, pr=10)

        ClimateDataFactory(city=self.city1, scenario=self.rcp45, climate_model=self.model1,
                           year=2003, day_of_year=1,
                           tasmax=10, tasmin=10, pr=10)

        ClimateDataFactory(city=self.city1, scenario=self.rcp85, climate_model=self.model1,
                           year=2000, day_of_year=1,
                           tasmax=30, tasmin=30, pr=30)

        ClimateDataFactory(city=self.city1, scenario=self.rcp85, climate_model=self.model2,
                           year=2000, day_of_year=1,
                           tasmax=40, tasmin=40, pr=40)
