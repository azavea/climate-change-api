from django.test import TestCase

from climate_data.models import ClimateModel
from climate_data.tests.mixins import ClimateDataSetupMixin
from indicators import indicators


class IndicatorTests(ClimateDataSetupMixin, object):

    indicator_class = None    # Override this in subclass to set the indicator to test
    indicator_name = ''
    units = None
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
        indicator = self.indicator_class(self.city1, self.rcp85, units=self.units)
        data = indicator.calculate()
        self.assertEqual(data, self.test_indicator_rcp85_equals)

    def test_indicator_rcp45(self):
        indicator = self.indicator_class(self.city1, self.rcp45, units=self.units)
        data = indicator.calculate()
        self.assertEqual(data, self.test_indicator_rcp45_equals)

    def test_indicator_no_data(self):
        indicator = self.indicator_class(self.city2, self.rcp85, units=self.units)
        data = indicator.calculate()
        self.assertEqual(data, self.test_indicator_no_data_equals)

    def test_years_filter(self):
        indicator = self.indicator_class(self.city1, self.rcp45,
                                         units=self.units, years='2001:2002')
        data = indicator.calculate()
        self.assertEqual(data, self.test_years_filter_equals)

    def test_models_filter(self):
        indicator = self.indicator_class(self.city1, self.rcp45, units=self.units, models='CCSM4')
        data = indicator.calculate()
        self.assertEqual(data, self.test_models_filter_equals)

    def test_unit_conversion_definitions(self):
        """ Some sanity checks for unit conversion class attributes """
        self.assertIn(self.indicator_class.default_units, self.indicator_class.available_units)
        storage_units = self.indicator_class.storage_units
        for units in self.indicator_class.available_units:
            self.assertTrue(units == storage_units or callable(
                self.indicator_class.conversions[self.indicator_class.storage_units][units]))


class TemperatureIndicatorTests(IndicatorTests):
    def test_unit_conversion(self):
        indicator = self.indicator_class(self.city1, self.rcp85, units='F')
        data = indicator.calculate()
        self.assertEqual(data, self.test_units_fahrenheit_equals,
                         'Temperature should be converted to degrees F')


class DailyHighTemperatureTestCase(TemperatureIndicatorTests, TestCase):
    indicator_class = indicators.DailyHighTemperature
    indicator_name = 'daily_high_temperature'
    units = 'K'
    test_indicator_rcp85_equals = {'2000-01-01': {'avg': 35.0, 'max': 40.0, 'min': 30.0}}
    test_indicator_rcp45_equals = {'2000-01-01': {'max': 20.0, 'avg': 15.0, 'min': 10.0},
                                   '2001-01-01': {'max': 20.0, 'avg': 15.0, 'min': 10.0},
                                   '2002-01-01': {'avg': 10.0, 'max': 10.0, 'min': 10.0},
                                   '2003-01-01': {'avg': 10.0, 'max': 10.0, 'min': 10.0}}
    test_years_filter_equals = {'2001-01-01': {'max': 20.0, 'avg': 15.0, 'min': 10.0},
                                '2002-01-01': {'avg': 10.0, 'max': 10.0, 'min': 10.0}}
    test_models_filter_equals = {'2000-01-01': {'avg': 10.0, 'max': 10.0, 'min': 10.0},
                                 '2001-01-01': {'avg': 10.0, 'max': 10.0, 'min': 10.0},
                                 '2002-01-01': {'avg': 10.0, 'max': 10.0, 'min': 10.0},
                                 '2003-01-01': {'avg': 10.0, 'max': 10.0, 'min': 10.0}}
    test_units_fahrenheit_equals = {'2000-01-01': {'avg': -396.67, 'max': -387.67, 'min': -405.67}}


class YearlyAverageHighTemperatureTestCase(TemperatureIndicatorTests, TestCase):
    indicator_class = indicators.YearlyAverageHighTemperature
    indicator_name = 'yearly_average_high_temperature'
    units = 'K'
    test_indicator_rcp85_equals = {2000: {'avg': 35.0, 'max': 40.0, 'min': 30.0}}
    test_indicator_rcp45_equals = {2000: {'max': 20.0, 'avg': 15.0, 'min': 10.0},
                                   2001: {'max': 20.0, 'avg': 15.0, 'min': 10.0},
                                   2002: {'avg': 10.0, 'max': 10.0, 'min': 10.0},
                                   2003: {'avg': 10.0, 'max': 10.0, 'min': 10.0}}
    test_years_filter_equals = {2001: {'max': 20.0, 'avg': 15.0, 'min': 10.0},
                                2002: {'avg': 10.0, 'max': 10.0, 'min': 10.0}}
    test_models_filter_equals = {2000: {'avg': 10.0, 'max': 10.0, 'min': 10.0},
                                 2001: {'avg': 10.0, 'max': 10.0, 'min': 10.0},
                                 2002: {'avg': 10.0, 'max': 10.0, 'min': 10.0},
                                 2003: {'avg': 10.0, 'max': 10.0, 'min': 10.0}}
    test_units_fahrenheit_equals = {2000: {'avg': -396.67, 'max': -387.67, 'min': -405.67}}


class YearlyAverageLowTemperatureTestCase(TemperatureIndicatorTests, TestCase):
    indicator_class = indicators.YearlyAverageLowTemperature
    indicator_name = 'yearly_average_low_temperature'
    units = 'K'
    test_indicator_rcp85_equals = {2000: {'avg': 35.0, 'max': 40.0, 'min': 30.0}}
    test_indicator_rcp45_equals = {2000: {'max': 20.0, 'avg': 15.0, 'min': 10.0},
                                   2001: {'max': 20.0, 'avg': 15.0, 'min': 10.0},
                                   2002: {'avg': 10.0, 'max': 10.0, 'min': 10.0},
                                   2003: {'avg': 10.0, 'max': 10.0, 'min': 10.0}}
    test_years_filter_equals = {2001: {'max': 20.0, 'avg': 15.0, 'min': 10.0},
                                2002: {'avg': 10.0, 'max': 10.0, 'min': 10.0}}
    test_models_filter_equals = {2000: {'avg': 10.0, 'max': 10.0, 'min': 10.0},
                                 2001: {'avg': 10.0, 'max': 10.0, 'min': 10.0},
                                 2002: {'avg': 10.0, 'max': 10.0, 'min': 10.0},
                                 2003: {'avg': 10.0, 'max': 10.0, 'min': 10.0}}
    test_units_fahrenheit_equals = {2000: {'avg': -396.67, 'max': -387.67, 'min': -405.67}}


class YearlyMaxHighTemperatureTestCase(TemperatureIndicatorTests, TestCase):
    indicator_class = indicators.YearlyMaxHighTemperature
    indicator_name = 'yearly_max_high_temperature'
    units = 'K'
    test_indicator_rcp85_equals = {2000: {'avg': 35.0, 'max': 40.0, 'min': 30.0}}
    test_indicator_rcp45_equals = {2000: {'max': 20.0, 'avg': 15.0, 'min': 10.0},
                                   2001: {'max': 20.0, 'avg': 15.0, 'min': 10.0},
                                   2002: {'avg': 10.0, 'max': 10.0, 'min': 10.0},
                                   2003: {'avg': 10.0, 'max': 10.0, 'min': 10.0}}
    test_years_filter_equals = {2001: {'max': 20.0, 'avg': 15.0, 'min': 10.0},
                                2002: {'avg': 10.0, 'max': 10.0, 'min': 10.0}}
    test_models_filter_equals = {2000: {'avg': 10.0, 'max': 10.0, 'min': 10.0},
                                 2001: {'avg': 10.0, 'max': 10.0, 'min': 10.0},
                                 2002: {'avg': 10.0, 'max': 10.0, 'min': 10.0},
                                 2003: {'avg': 10.0, 'max': 10.0, 'min': 10.0}}
    test_units_fahrenheit_equals = {2000: {'avg': -396.67, 'max': -387.67, 'min': -405.67}}


class YearlyMinLowTemperatureTestCase(TemperatureIndicatorTests, TestCase):
    indicator_class = indicators.YearlyMinLowTemperature
    indicator_name = 'yearly_min_low_temperature'
    units = 'K'
    test_indicator_rcp85_equals = {2000: {'avg': 35.0, 'max': 40.0, 'min': 30.0}}
    test_indicator_rcp45_equals = {2000: {'max': 20.0, 'avg': 15.0, 'min': 10.0},
                                   2001: {'max': 20.0, 'avg': 15.0, 'min': 10.0},
                                   2002: {'avg': 10.0, 'max': 10.0, 'min': 10.0},
                                   2003: {'avg': 10.0, 'max': 10.0, 'min': 10.0}}
    test_years_filter_equals = {2001: {'max': 20.0, 'avg': 15.0, 'min': 10.0},
                                2002: {'avg': 10.0, 'max': 10.0, 'min': 10.0}}
    test_models_filter_equals = {2000: {'avg': 10.0, 'max': 10.0, 'min': 10.0},
                                 2001: {'avg': 10.0, 'max': 10.0, 'min': 10.0},
                                 2002: {'avg': 10.0, 'max': 10.0, 'min': 10.0},
                                 2003: {'avg': 10.0, 'max': 10.0, 'min': 10.0}}
    test_units_fahrenheit_equals = {2000: {'avg': -396.67, 'max': -387.67, 'min': -405.67}}


class YearlyTotalPrecipitationTestCase(IndicatorTests, TestCase):
    indicator_class = indicators.YearlyTotalPrecipitation
    indicator_name = 'yearly_total_precipitation'
    units = 'kg*m^2/s'
    test_indicator_rcp85_equals = {2000: {'avg': 35.0, 'min': 30.0, 'max': 40.0}}
    test_indicator_rcp45_equals = {2000: {'max': 20.0, 'avg': 15.0, 'min': 10.0},
                                   2001: {'max': 20.0, 'avg': 15.0, 'min': 10.0},
                                   2002: {'avg': 10.0, 'max': 10.0, 'min': 10.0},
                                   2003: {'avg': 0.0, 'max': 0.0, 'min': 0.0}}
    test_years_filter_equals = {2001: {'max': 20.0, 'avg': 15.0, 'min': 10.0},
                                2002: {'avg': 10.0, 'max': 10.0, 'min': 10.0}}
    test_models_filter_equals = {2000: {'avg': 10.0, 'max': 10.0, 'min': 10.0},
                                 2001: {'avg': 10.0, 'max': 10.0, 'min': 10.0},
                                 2002: {'avg': 10.0, 'max': 10.0, 'min': 10.0},
                                 2003: {'avg': 0.0, 'max': 0.0, 'min': 0.0}}


class YearlyFrostDaysTestCase(IndicatorTests, TestCase):
    indicator_class = indicators.YearlyFrostDays
    indicator_name = 'yearly_frost_days'
    test_indicator_rcp85_equals = {2000: {'avg': 1, 'min': 1, 'max': 1}}
    test_indicator_rcp45_equals = {2000: {'avg': 1, 'min': 1, 'max': 1},
                                   2001: {'avg': 1, 'min': 1, 'max': 1},
                                   2002: {'avg': 1, 'min': 1, 'max': 1},
                                   2003: {'avg': 1, 'min': 1, 'max': 1}}
    test_years_filter_equals = {2001: {'avg': 1, 'min': 1, 'max': 1},
                                2002: {'avg': 1, 'min': 1, 'max': 1}}
    test_models_filter_equals = {2000: {'avg': 1, 'min': 1, 'max': 1},
                                 2001: {'avg': 1, 'min': 1, 'max': 1},
                                 2002: {'avg': 1, 'min': 1, 'max': 1},
                                 2003: {'avg': 1, 'min': 1, 'max': 1}}


class YearlyMaxConsecutiveDryDaysTestCase(IndicatorTests, TestCase):
    indicator_class = indicators.YearlyMaxConsecutiveDryDays
    indicator_name = 'yearly_max_consecutive_dry_days'
    test_indicator_rcp85_equals = {2000: {'avg': 0, 'min': 0, 'max': 0}}
    test_indicator_rcp45_equals = {2000: {'avg': 0, 'min': 0, 'max': 0},
                                   2001: {'avg': 0, 'min': 0, 'max': 0},
                                   2002: {'avg': 0, 'min': 0, 'max': 0},
                                   2003: {'avg': 1, 'min': 1, 'max': 1}}
    test_years_filter_equals = {2001: {'avg': 0, 'min': 0, 'max': 0},
                                2002: {'avg': 0, 'min': 0, 'max': 0}}
    test_models_filter_equals = {2000: {'avg': 0, 'min': 0, 'max': 0},
                                 2001: {'avg': 0, 'min': 0, 'max': 0},
                                 2002: {'avg': 0, 'min': 0, 'max': 0},
                                 2003: {'avg': 1, 'min': 1, 'max': 1}}


class YearlyDrySpellsTestCase(IndicatorTests, TestCase):
    indicator_class = indicators.YearlyDrySpells
    indicator_name = 'yearly_dry_spells'
    test_indicator_rcp85_equals = {2000: {'avg': 0, 'min': 0, 'max': 0}}
    test_indicator_rcp45_equals = {2000: {'avg': 0, 'min': 0, 'max': 0},
                                   2001: {'avg': 0, 'min': 0, 'max': 0},
                                   2002: {'avg': 0, 'min': 0, 'max': 0},
                                   2003: {'avg': 0, 'min': 0, 'max': 0}}
    test_years_filter_equals = {2001: {'avg': 0, 'min': 0, 'max': 0},
                                2002: {'avg': 0, 'min': 0, 'max': 0}}
    test_models_filter_equals = {2000: {'avg': 0, 'min': 0, 'max': 0},
                                 2001: {'avg': 0, 'min': 0, 'max': 0},
                                 2002: {'avg': 0, 'min': 0, 'max': 0},
                                 2003: {'avg': 0, 'min': 0, 'max': 0}}
