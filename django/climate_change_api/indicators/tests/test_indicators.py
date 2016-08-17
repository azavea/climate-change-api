from django.test import TestCase

from climate_data.tests.mixins import ClimateDataSetupMixin
from indicators import indicators


class IndicatorTests(ClimateDataSetupMixin, object):

    indicator_class = None    # Override this in subclass to set the indicator to test
    test_indicator_no_data_equals = {}
    test_indicator_rcp85_equals = None
    test_indicator_rcp45_equals = None
    test_years_filter_equals = None
    test_models_filter_equals = None

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
                                                           models='model1')
        data = indicator.calculate()
        self.assertEqual(data, self.test_models_filter_equals)


class YearlyAverageMaxTemperatureTestCase(IndicatorTests, TestCase):

    indicator_class = indicators.YearlyAverageMaxTemperature
    test_indicator_rcp85_equals = {2000: 35.0}
    test_indicator_rcp45_equals = {2000: 15.0, 2001: 15.0, 2002: 10.0, 2003: 10.0}
    test_years_filter_equals = {2001: 15.0, 2002: 10.0}
    test_models_filter_equals = {2000: 10.0, 2001: 10.0, 2002: 10.0, 2003: 10.0}


class YearlyAverageMinTemperatureTestCase(IndicatorTests, TestCase):

    indicator_class = indicators.YearlyAverageMinTemperature
    test_indicator_rcp85_equals = {2000: 35.0}
    test_indicator_rcp45_equals = {2000: 15.0, 2001: 15.0, 2002: 10.0, 2003: 10.0}
    test_years_filter_equals = {2001: 15.0, 2002: 10.0}
    test_models_filter_equals = {2000: 10.0, 2001: 10.0, 2002: 10.0, 2003: 10.0}
