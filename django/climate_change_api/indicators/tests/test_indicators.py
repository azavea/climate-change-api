from django.test import TestCase

from climate_data.models import ClimateModel
from climate_data.tests.mixins import ClimateDataSetupMixin
from indicators import indicators


class IndicatorTests(ClimateDataSetupMixin, object):

    indicator_class = None    # Override this in subclass to set the indicator to test
    parameters = None
    indicator_name = ''
    units = None
    time_aggregation = None
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
        indicator = self.indicator_class(self.city1, self.rcp85, parameters=self.parameters,
                                         units=self.units, time_aggregation=self.time_aggregation)
        data = indicator.calculate()
        self.assertEqual(data, self.test_indicator_rcp85_equals)

    def test_indicator_rcp45(self):
        indicator = self.indicator_class(self.city1, self.rcp45, parameters=self.parameters,
                                         units=self.units, time_aggregation=self.time_aggregation)
        data = indicator.calculate()
        self.assertEqual(data, self.test_indicator_rcp45_equals)

    def test_indicator_no_data(self):
        indicator = self.indicator_class(self.city2, self.rcp85, parameters=self.parameters,
                                         units=self.units, time_aggregation=self.time_aggregation)
        data = indicator.calculate()
        self.assertEqual(data, self.test_indicator_no_data_equals)

    def test_years_filter(self):
        indicator = self.indicator_class(self.city1, self.rcp45,  parameters=self.parameters,
                                         units=self.units, time_aggregation=self.time_aggregation,
                                         years='2001:2002')
        data = indicator.calculate()
        self.assertEqual(data, self.test_years_filter_equals)

    def test_models_filter(self):
        indicator = self.indicator_class(self.city1, self.rcp45, models='CCSM4',
                                         parameters=self.parameters, units=self.units,
                                         time_aggregation=self.time_aggregation)
        data = indicator.calculate()
        self.assertEqual(data, self.test_models_filter_equals)

    def test_unit_conversion_definitions(self):
        """ Some sanity checks for unit conversion class attributes """
        self.assertIn(self.indicator_class.default_units, self.indicator_class.available_units)


class TemperatureIndicatorTests(IndicatorTests):
    def test_unit_conversion(self):
        indicator = self.indicator_class(self.city1, self.rcp85,
                                         time_aggregation=self.time_aggregation, units='F')
        data = indicator.calculate()
        self.assertEqual(data, self.test_units_fahrenheit_equals,
                         'Temperature should be converted to degrees F')


class DailyHighTemperatureTestCase(TemperatureIndicatorTests, TestCase):
    indicator_class = indicators.HighTemperature
    indicator_name = 'high_temperature'
    time_aggregation = 'daily'
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
    indicator_class = indicators.AverageHighTemperature
    indicator_name = 'average_high_temperature'
    time_aggregation = 'yearly'
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
    indicator_class = indicators.AverageLowTemperature
    indicator_name = 'average_low_temperature'
    time_aggregation = 'yearly'
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
    indicator_class = indicators.MaxHighTemperature
    indicator_name = 'max_high_temperature'
    time_aggregation = 'yearly'
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
    indicator_class = indicators.MinLowTemperature
    indicator_name = 'min_low_temperature'
    time_aggregation = 'yearly'
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
    indicator_class = indicators.TotalPrecipitation
    indicator_name = 'total_precipitation'
    time_aggregation = 'yearly'
    units = 'kg/m^2/s'
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
    indicator_class = indicators.FrostDays
    indicator_name = 'frost_days'
    time_aggregation = 'yearly'
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
    time_aggregation = 'yearly'
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
    time_aggregation = 'yearly'
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


class YearlyExtremePrecipitationEventsTestCase(IndicatorTests, TestCase):
    indicator_class = indicators.ExtremePrecipitationEvents
    indicator_name = 'extreme_precipitation_events'
    time_aggregation = 'yearly'
    test_indicator_rcp85_equals = {2000: {'avg': 1, 'min': 1, 'max': 1}}
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


class YearlyExtremeHeatEventsTestCase(IndicatorTests, TestCase):
    indicator_class = indicators.ExtremeHeatEvents
    indicator_name = 'extreme_heat_events'
    time_aggregation = 'yearly'
    test_indicator_rcp85_equals = {2000: {'avg': 1, 'min': 1, 'max': 1}}
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


class YearlyExtremeColdEventsTestCase(IndicatorTests, TestCase):
    indicator_class = indicators.ExtremeColdEvents
    indicator_name = 'extreme_cold_events'
    time_aggregation = 'yearly'
    test_indicator_rcp85_equals = {2000: {'avg': 0, 'min': 0, 'max': 0}}
    test_indicator_rcp45_equals = {2000: {'avg': 0.5, 'min': 0, 'max': 1},
                                   2001: {'avg': 0.5, 'min': 0, 'max': 1},
                                   2002: {'avg': 1, 'min': 1, 'max': 1},
                                   2003: {'avg': 1, 'min': 1, 'max': 1}}
    test_years_filter_equals = {2001: {'avg': 0.5, 'min': 0, 'max': 1},
                                2002: {'avg': 1.0, 'min': 1, 'max': 1}}
    test_models_filter_equals = {2000: {'avg': 1.0, 'min': 1, 'max': 1},
                                 2001: {'avg': 1.0, 'min': 1, 'max': 1},
                                 2002: {'avg': 1.0, 'min': 1, 'max': 1},
                                 2003: {'avg': 1.0, 'min': 1, 'max': 1}}


class YearlyHeatingDegreeDaysTestCase(IndicatorTests, TestCase):
    indicator_class = indicators.HeatingDegreeDays
    indicator_name = 'heating_degree_days'
    time_aggregation = 'yearly'
    parameters = {
        'basetemp': '42.5K'
    }
    test_indicator_rcp85_equals = {2000: {'avg': 13.5, 'min': 4.5, 'max': 22.5}}
    test_indicator_rcp45_equals = {2000: {'avg': 49.5, 'min': 40.5, 'max': 58.5},
                                   2001: {'avg': 49.5, 'min': 40.5, 'max': 58.5},
                                   2002: {'avg': 58.5, 'min': 58.5, 'max': 58.5},
                                   2003: {'avg': 58.5, 'min': 58.5, 'max': 58.5}}
    test_years_filter_equals = {2001: {'avg': 49.5, 'min': 40.5, 'max': 58.5},
                                2002: {'avg': 58.5, 'min': 58.5, 'max': 58.5}}
    test_models_filter_equals = {2000: {'avg': 58.5, 'min': 58.5, 'max': 58.5},
                                 2001: {'avg': 58.5, 'min': 58.5, 'max': 58.5},
                                 2002: {'avg': 58.5, 'min': 58.5, 'max': 58.5},
                                 2003: {'avg': 58.5, 'min': 58.5, 'max': 58.5}}


class YearlyCoolingDegreeDaysTestCase(IndicatorTests, TestCase):
    indicator_class = indicators.CoolingDegreeDays
    indicator_name = 'cooling_degree_days'
    time_aggregation = 'yearly'
    parameters = {
        'basetemp': '-265.85C'  # 7.3K
    }
    test_indicator_rcp85_equals = {2000: {'avg': 49.86, 'min': 40.86, 'max': 58.86000000000001}}
    test_indicator_rcp45_equals = {2000: {'avg': 13.860000000000046, 'min': 4.86000000000009,
                                          'max': 22.86},
                                   2001: {'avg': 13.860000000000046, 'min': 4.86000000000009,
                                          'max': 22.86},
                                   2002: {'avg': 4.86000000000009, 'min': 4.86000000000009,
                                          'max': 4.86000000000009},
                                   2003: {'avg': 4.86000000000009, 'min': 4.86000000000009,
                                          'max': 4.86000000000009}}
    test_years_filter_equals = {2001: {'avg': 13.860000000000046, 'min': 4.86000000000009,
                                       'max': 22.86},
                                2002: {'avg': 4.86000000000009, 'min': 4.86000000000009,
                                       'max': 4.86000000000009}}
    test_models_filter_equals = {2000: {'avg': 4.86000000000009, 'min': 4.86000000000009,
                                        'max': 4.86000000000009},
                                 2001: {'avg': 4.86000000000009, 'min': 4.86000000000009,
                                        'max': 4.86000000000009},
                                 2002: {'avg': 4.86000000000009, 'min': 4.86000000000009,
                                        'max': 4.86000000000009},
                                 2003: {'avg': 4.86000000000009, 'min': 4.86000000000009,
                                        'max': 4.86000000000009}}


class MonthlyAverageHighTemperatureTestCase(TemperatureIndicatorTests, TestCase):
    indicator_class = indicators.AverageHighTemperature
    indicator_name = 'average_high_temperature'
    time_aggregation = 'monthly'
    units = 'K'
    test_indicator_rcp85_equals = {'2000-01': {'avg': 35.0, 'max': 40.0, 'min': 30.0}}
    test_indicator_rcp45_equals = {'2000-01': {'max': 20.0, 'avg': 15.0, 'min': 10.0},
                                   '2001-01': {'max': 20.0, 'avg': 15.0, 'min': 10.0},
                                   '2002-01': {'avg': 10.0, 'max': 10.0, 'min': 10.0},
                                   '2003-01': {'avg': 10.0, 'max': 10.0, 'min': 10.0}}
    test_years_filter_equals = {'2001-01': {'max': 20.0, 'avg': 15.0, 'min': 10.0},
                                '2002-01': {'avg': 10.0, 'max': 10.0, 'min': 10.0}}
    test_models_filter_equals = {'2000-01': {'avg': 10.0, 'max': 10.0, 'min': 10.0},
                                 '2001-01': {'avg': 10.0, 'max': 10.0, 'min': 10.0},
                                 '2002-01': {'avg': 10.0, 'max': 10.0, 'min': 10.0},
                                 '2003-01': {'avg': 10.0, 'max': 10.0, 'min': 10.0}}
    test_units_fahrenheit_equals = {'2000-01': {'avg': -396.67, 'max': -387.67, 'min': -405.67}}


class MonthlyAverageLowTemperatureTestCase(TemperatureIndicatorTests, TestCase):
    indicator_class = indicators.AverageLowTemperature
    indicator_name = 'average_low_temperature'
    time_aggregation = 'monthly'
    units = 'K'
    test_indicator_rcp85_equals = {'2000-01': {'avg': 35.0, 'max': 40.0, 'min': 30.0}}
    test_indicator_rcp45_equals = {'2000-01': {'max': 20.0, 'avg': 15.0, 'min': 10.0},
                                   '2001-01': {'max': 20.0, 'avg': 15.0, 'min': 10.0},
                                   '2002-01': {'avg': 10.0, 'max': 10.0, 'min': 10.0},
                                   '2003-01': {'avg': 10.0, 'max': 10.0, 'min': 10.0}}
    test_years_filter_equals = {'2001-01': {'max': 20.0, 'avg': 15.0, 'min': 10.0},
                                '2002-01': {'avg': 10.0, 'max': 10.0, 'min': 10.0}}
    test_models_filter_equals = {'2000-01': {'avg': 10.0, 'max': 10.0, 'min': 10.0},
                                 '2001-01': {'avg': 10.0, 'max': 10.0, 'min': 10.0},
                                 '2002-01': {'avg': 10.0, 'max': 10.0, 'min': 10.0},
                                 '2003-01': {'avg': 10.0, 'max': 10.0, 'min': 10.0}}
    test_units_fahrenheit_equals = {'2000-01': {'avg': -396.67, 'max': -387.67, 'min': -405.67}}


class MonthlyMaxHighTemperatureTestCase(TemperatureIndicatorTests, TestCase):
    indicator_class = indicators.MaxHighTemperature
    indicator_name = 'max_high_temperature'
    time_aggregation = 'monthly'
    units = 'K'
    test_indicator_rcp85_equals = {'2000-01': {'avg': 35.0, 'max': 40.0, 'min': 30.0}}
    test_indicator_rcp45_equals = {'2000-01': {'max': 20.0, 'avg': 15.0, 'min': 10.0},
                                   '2001-01': {'max': 20.0, 'avg': 15.0, 'min': 10.0},
                                   '2002-01': {'avg': 10.0, 'max': 10.0, 'min': 10.0},
                                   '2003-01': {'avg': 10.0, 'max': 10.0, 'min': 10.0}}
    test_years_filter_equals = {'2001-01': {'max': 20.0, 'avg': 15.0, 'min': 10.0},
                                '2002-01': {'avg': 10.0, 'max': 10.0, 'min': 10.0}}
    test_models_filter_equals = {'2000-01': {'avg': 10.0, 'max': 10.0, 'min': 10.0},
                                 '2001-01': {'avg': 10.0, 'max': 10.0, 'min': 10.0},
                                 '2002-01': {'avg': 10.0, 'max': 10.0, 'min': 10.0},
                                 '2003-01': {'avg': 10.0, 'max': 10.0, 'min': 10.0}}
    test_units_fahrenheit_equals = {'2000-01': {'avg': -396.67, 'max': -387.67, 'min': -405.67}}


class MonthlyMinLowTemperatureTestCase(TemperatureIndicatorTests, TestCase):
    indicator_class = indicators.MinLowTemperature
    indicator_name = 'min_low_temperature'
    time_aggregation = 'monthly'
    units = 'K'
    test_indicator_rcp85_equals = {'2000-01': {'avg': 35.0, 'max': 40.0, 'min': 30.0}}
    test_indicator_rcp45_equals = {'2000-01': {'max': 20.0, 'avg': 15.0, 'min': 10.0},
                                   '2001-01': {'max': 20.0, 'avg': 15.0, 'min': 10.0},
                                   '2002-01': {'avg': 10.0, 'max': 10.0, 'min': 10.0},
                                   '2003-01': {'avg': 10.0, 'max': 10.0, 'min': 10.0}}
    test_years_filter_equals = {'2001-01': {'max': 20.0, 'avg': 15.0, 'min': 10.0},
                                '2002-01': {'avg': 10.0, 'max': 10.0, 'min': 10.0}}
    test_models_filter_equals = {'2000-01': {'avg': 10.0, 'max': 10.0, 'min': 10.0},
                                 '2001-01': {'avg': 10.0, 'max': 10.0, 'min': 10.0},
                                 '2002-01': {'avg': 10.0, 'max': 10.0, 'min': 10.0},
                                 '2003-01': {'avg': 10.0, 'max': 10.0, 'min': 10.0}}
    test_units_fahrenheit_equals = {'2000-01': {'avg': -396.67, 'max': -387.67, 'min': -405.67}}


class MonthlyTotalPrecipitationTestCase(IndicatorTests, TestCase):
    indicator_class = indicators.TotalPrecipitation
    indicator_name = 'total_precipitation'
    time_aggregation = 'monthly'
    units = 'kg/m^2/s'
    test_indicator_rcp85_equals = {'2000-01': {'avg': 35.0, 'min': 30.0, 'max': 40.0}}
    test_indicator_rcp45_equals = {'2000-01': {'max': 20.0, 'avg': 15.0, 'min': 10.0},
                                   '2001-01': {'max': 20.0, 'avg': 15.0, 'min': 10.0},
                                   '2002-01': {'avg': 10.0, 'max': 10.0, 'min': 10.0},
                                   '2003-01': {'avg': 0.0, 'max': 0.0, 'min': 0.0}}
    test_years_filter_equals = {'2001-01': {'max': 20.0, 'avg': 15.0, 'min': 10.0},
                                '2002-01': {'avg': 10.0, 'max': 10.0, 'min': 10.0}}
    test_models_filter_equals = {'2000-01': {'avg': 10.0, 'max': 10.0, 'min': 10.0},
                                 '2001-01': {'avg': 10.0, 'max': 10.0, 'min': 10.0},
                                 '2002-01': {'avg': 10.0, 'max': 10.0, 'min': 10.0},
                                 '2003-01': {'avg': 0.0, 'max': 0.0, 'min': 0.0}}


class MonthlyFrostDaysTestCase(IndicatorTests, TestCase):
    indicator_class = indicators.FrostDays
    indicator_name = 'frost_days'
    time_aggregation = 'monthly'
    test_indicator_rcp85_equals = {'2000-01': {'avg': 1, 'min': 1, 'max': 1}}
    test_indicator_rcp45_equals = {'2000-01': {'avg': 1, 'min': 1, 'max': 1},
                                   '2001-01': {'avg': 1, 'min': 1, 'max': 1},
                                   '2002-01': {'avg': 1, 'min': 1, 'max': 1},
                                   '2003-01': {'avg': 1, 'min': 1, 'max': 1}}
    test_years_filter_equals = {'2001-01': {'avg': 1, 'min': 1, 'max': 1},
                                '2002-01': {'avg': 1, 'min': 1, 'max': 1}}
    test_models_filter_equals = {'2000-01': {'avg': 1, 'min': 1, 'max': 1},
                                 '2001-01': {'avg': 1, 'min': 1, 'max': 1},
                                 '2002-01': {'avg': 1, 'min': 1, 'max': 1},
                                 '2003-01': {'avg': 1, 'min': 1, 'max': 1}}


class MonthlyExtremePrecipitationEventsTestCase(IndicatorTests, TestCase):
    indicator_class = indicators.ExtremePrecipitationEvents
    indicator_name = 'extreme_precipitation_events'
    time_aggregation = 'monthly'
    test_indicator_rcp85_equals = {'2000-01': {'avg': 1.0, 'min': 1, 'max': 1}}
    test_indicator_rcp45_equals = {'2000-01': {'avg': 0.0, 'min': 0, 'max': 0},
                                   '2001-01': {'avg': 0.0, 'min': 0, 'max': 0},
                                   '2002-01': {'avg': 0.0, 'min': 0, 'max': 0},
                                   '2003-01': {'avg': 0.0, 'min': 0, 'max': 0}}
    test_years_filter_equals = {'2001-01': {'avg': 0.0, 'min': 0, 'max': 0},
                                '2002-01': {'avg': 0.0, 'min': 0, 'max': 0}}
    test_models_filter_equals = {'2000-01': {'avg': 0.0, 'min': 0, 'max': 0},
                                 '2001-01': {'avg': 0.0, 'min': 0, 'max': 0},
                                 '2002-01': {'avg': 0.0, 'min': 0, 'max': 0},
                                 '2003-01': {'avg': 0.0, 'min': 0, 'max': 0}}


class MonthlyExtremeHeatEventsTestCase(IndicatorTests, TestCase):
    indicator_class = indicators.ExtremeHeatEvents
    indicator_name = 'extreme_heat_events'
    time_aggregation = 'monthly'
    test_indicator_rcp85_equals = {'2000-01': {'avg': 1.0, 'min': 1, 'max': 1}}
    test_indicator_rcp45_equals = {'2000-01': {'avg': 0.0, 'min': 0, 'max': 0},
                                   '2001-01': {'avg': 0.0, 'min': 0, 'max': 0},
                                   '2002-01': {'avg': 0.0, 'min': 0, 'max': 0},
                                   '2003-01': {'avg': 0.0, 'min': 0, 'max': 0}}
    test_years_filter_equals = {'2001-01': {'avg': 0.0, 'min': 0, 'max': 0},
                                '2002-01': {'avg': 0.0, 'min': 0, 'max': 0}}
    test_models_filter_equals = {'2000-01': {'avg': 0.0, 'min': 0, 'max': 0},
                                 '2001-01': {'avg': 0.0, 'min': 0, 'max': 0},
                                 '2002-01': {'avg': 0.0, 'min': 0, 'max': 0},
                                 '2003-01': {'avg': 0.0, 'min': 0, 'max': 0}}


class MonthlyExtremeColdEventsTestCase(IndicatorTests, TestCase):
    indicator_class = indicators.ExtremeColdEvents
    indicator_name = 'extreme_cold_events'
    time_aggregation = 'monthly'
    test_indicator_rcp85_equals = {'2000-01': {'avg': 0.0, 'min': 0, 'max': 0}}
    test_indicator_rcp45_equals = {'2000-01': {'avg': 0.5, 'min': 0, 'max': 1},
                                   '2001-01': {'avg': 0.5, 'min': 0, 'max': 1},
                                   '2002-01': {'avg': 1.0, 'min': 1, 'max': 1},
                                   '2003-01': {'avg': 1.0, 'min': 1, 'max': 1}}
    test_years_filter_equals = {'2001-01': {'avg': 0.5, 'min': 0, 'max': 1},
                                '2002-01': {'avg': 1.0, 'min': 1, 'max': 1}}
    test_models_filter_equals = {'2000-01': {'avg': 1.0, 'min': 1, 'max': 1},
                                 '2001-01': {'avg': 1.0, 'min': 1, 'max': 1},
                                 '2002-01': {'avg': 1.0, 'min': 1, 'max': 1},
                                 '2003-01': {'avg': 1.0, 'min': 1, 'max': 1}}


class MonthlyHeatingDegreeDaysTestCase(IndicatorTests, TestCase):
    indicator_class = indicators.HeatingDegreeDays
    indicator_name = 'heating_degree_days'
    time_aggregation = 'monthly'
    parameters = {
        'basetemp': '-384.07',
        'units': 'F'
    }
    test_indicator_rcp85_equals = {'2000-01': {'avg': 12.60000000000001,
                                               'min': 3.6000000000000183, 'max': 21.6}}
    test_indicator_rcp45_equals = {'2000-01': {'avg': 48.6, 'min': 39.6, 'max': 57.6},
                                   '2001-01': {'avg': 48.6, 'min': 39.6, 'max': 57.6},
                                   '2002-01': {'avg': 57.6, 'min': 57.6, 'max': 57.6},
                                   '2003-01': {'avg': 57.6, 'min': 57.6, 'max': 57.6}}
    test_years_filter_equals = {'2001-01': {'avg': 48.6, 'min': 39.6, 'max': 57.6},
                                '2002-01': {'avg': 57.6, 'min': 57.6, 'max': 57.6}}
    test_models_filter_equals = {'2000-01': {'avg': 57.6, 'min': 57.6, 'max': 57.6},
                                 '2001-01': {'avg': 57.6, 'min': 57.6, 'max': 57.6},
                                 '2002-01': {'avg': 57.6, 'min': 57.6, 'max': 57.6},
                                 '2003-01': {'avg': 57.6, 'min': 57.6, 'max': 57.6}}


class MonthlyCoolingDegreeDaysTestCase(IndicatorTests, TestCase):
    indicator_class = indicators.CoolingDegreeDays
    indicator_name = 'cooling_degree_days'
    time_aggregation = 'monthly'
    parameters = {
        'basetemp': '-273.15',
        'units': 'C'
    }
    test_indicator_rcp85_equals = {'2000-01': {'avg': 63.0, 'min': 54.0, 'max': 72.0}}
    test_indicator_rcp45_equals = {'2000-01': {'avg': 27.0, 'min': 18.0, 'max': 36.0},
                                   '2001-01': {'avg': 27.0, 'min': 18.0, 'max': 36.0},
                                   '2002-01': {'avg': 18.0, 'min': 18.0, 'max': 18.0},
                                   '2003-01': {'avg': 18.0, 'min': 18.0, 'max': 18.0}}
    test_years_filter_equals = {'2001-01': {'avg': 27.0, 'min': 18.0, 'max': 36.0},
                                '2002-01': {'avg': 18.0, 'min': 18.0, 'max': 18.0}}
    test_models_filter_equals = {'2000-01': {'avg': 18.0, 'min': 18.0, 'max': 18.0},
                                 '2001-01': {'avg': 18.0, 'min': 18.0, 'max': 18.0},
                                 '2002-01': {'avg': 18.0, 'min': 18.0, 'max': 18.0},
                                 '2003-01': {'avg': 18.0, 'min': 18.0, 'max': 18.0}}
