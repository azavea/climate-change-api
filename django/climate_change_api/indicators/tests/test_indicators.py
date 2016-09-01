from django.test import TestCase

from climate_data.models import ClimateModel
from climate_data.tests.mixins import ClimateDataSetupMixin
from indicators import indicators


class IndicatorTests(ClimateDataSetupMixin, object):

    indicator_class = None    # Override this in subclass to set the indicator to test
    indicator_name = ''
    test_indicator_no_data_equals = {}
    test_indicator_rcp85_equals = None
    test_indicator_rcp45_equals = None
    test_years_filter_equals = None
    test_models_filter_equals = None
    test_units_fahrenheit_equals = None

    def test_indicator_name(self):
        self.assertEqual(self.indicator_class.name(), self.indicator_name)

    def test_indicator_description(self):
        self.assertTrue(len(self.indicator_class.description) > 0)

    def test_indicator_rcp85(self):
        indicator = self.indicator_class(self.city1, self.rcp85)
        data = indicator.calculate()
        self.assertEqual(data, self.test_indicator_rcp85_equals)

    def test_indicator_rcp45(self):
        indicator = self.indicator_class(self.city1, self.rcp45)
        data = indicator.calculate()
        self.assertEqual(data, self.test_indicator_rcp45_equals)

    def test_indicator_no_data(self):
        indicator = self.indicator_class(self.city2, self.rcp85)
        data = indicator.calculate()
        self.assertEqual(data, self.test_indicator_no_data_equals)

    def test_years_filter(self):
        indicator = indicators.YearlyAverageMaxTemperature(self.city1,
                                                           self.rcp45,
                                                           years='2001:2002')
        data = indicator.calculate()
        self.assertEqual(data, self.test_years_filter_equals)

    def test_models_filter(self):
        indicator = indicators.YearlyAverageMaxTemperature(self.city1,
                                                           self.rcp45,
                                                           models='CCSM4')
        data = indicator.calculate()
        self.assertEqual(data, self.test_models_filter_equals)

    def test_unit_conversion(self):
        indicator = self.indicator_class(self.city1, self.rcp85, units='F')
        data = indicator.calculate()
        self.assertEqual(data, self.test_units_fahrenheit_equals,
                         'Temperature should be converted to degrees F')


class YearlyAverageMaxTemperatureTestCase(IndicatorTests, TestCase):

    indicator_class = indicators.YearlyAverageMaxTemperature
    indicator_name = 'yearly_average_max_temperature'
    test_indicator_rcp85_equals = {2000: 35.0}
    test_indicator_rcp45_equals = {2000: 15.0, 2001: 15.0, 2002: 10.0, 2003: 10.0}
    test_years_filter_equals = {2001: 15.0, 2002: 10.0}
    test_models_filter_equals = {2000: 10.0, 2001: 10.0, 2002: 10.0, 2003: 10.0}
    test_units_fahrenheit_equals = {2000: -396.67}


class YearlyAverageMinTemperatureTestCase(IndicatorTests, TestCase):

    indicator_class = indicators.YearlyAverageMinTemperature
    indicator_name = 'yearly_average_min_temperature'
    test_indicator_rcp85_equals = {2000: 35.0}
    test_indicator_rcp45_equals = {2000: 15.0, 2001: 15.0, 2002: 10.0, 2003: 10.0}
    test_years_filter_equals = {2001: 15.0, 2002: 10.0}
    test_models_filter_equals = {2000: 10.0, 2001: 10.0, 2002: 10.0, 2003: 10.0}
    test_units_fahrenheit_equals = {2000: -396.67}
