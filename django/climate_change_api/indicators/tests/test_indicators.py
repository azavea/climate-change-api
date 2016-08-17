from django.test import TestCase

from climate_data.tests.mixins import ClimateDataSetupMixin
from indicators import indicators


class YearlyAverageMaxTemperatureTestCase(ClimateDataSetupMixin, TestCase):

    def test_indicator_rcp85(self):
        indicator = indicators.YearlyAverageMaxTemperature(self.city1, self.rcp85)
        data = indicator.calculate()
        self.assertEqual(data, {2000: 35.0})

    def test_indicator_rcp45(self):
        indicator = indicators.YearlyAverageMaxTemperature(self.city1, self.rcp45)
        data = indicator.calculate()
        self.assertEqual(data, {2000: 15.0, 2001: 15.0, 2002: 10.0, 2003: 10.0})

    def test_indicator_no_data(self):
        indicator = indicators.YearlyAverageMaxTemperature(self.city2, self.rcp85)
        data = indicator.calculate()
        self.assertEqual(data, {})

    def test_years_filter(self):
        indicator = indicators.YearlyAverageMaxTemperature(self.city1,
                                                           self.rcp45,
                                                           years='2001:2002')
        data = indicator.calculate()
        self.assertEqual(data, {2001: 15.0, 2002: 10.0})

    def test_models_filter(self):
        indicator = indicators.YearlyAverageMaxTemperature(self.city1,
                                                           self.rcp45,
                                                           models='model1')
        data = indicator.calculate()
        self.assertEqual(data, {2000: 10.0, 2001: 10.0, 2002: 10.0, 2003: 10.0})


class YearlyAverageMinTemperatureTestCase(ClimateDataSetupMixin, TestCase):

    def test_indicator_rcp85(self):

        indicator = indicators.YearlyAverageMinTemperature(self.city1, self.rcp85)
        data = indicator.calculate()
        self.assertEqual(data, {2000: 35.0})

    def test_indicator_rcp45(self):
        indicator = indicators.YearlyAverageMinTemperature(self.city1, self.rcp45)
        data = indicator.calculate()
        self.assertEqual(data, {2000: 15.0, 2001: 15.0, 2002: 10.0, 2003: 10.0})

    def test_indicator_no_data(self):
        indicator = indicators.YearlyAverageMinTemperature(self.city2, self.rcp85)
        data = indicator.calculate()
        self.assertEqual(data, {})

    def test_years_filter(self):
        indicator = indicators.YearlyAverageMinTemperature(self.city1,
                                                           self.rcp45,
                                                           years='2001:2002')
        data = indicator.calculate()
        self.assertEqual(data, {2001: 15.0, 2002: 10.0})

    def test_models_filter(self):
        indicator = indicators.YearlyAverageMinTemperature(self.city1,
                                                           self.rcp45,
                                                           models='model1')
        data = indicator.calculate()
        self.assertEqual(data, {2000: 10.0, 2001: 10.0, 2002: 10.0, 2003: 10.0})
