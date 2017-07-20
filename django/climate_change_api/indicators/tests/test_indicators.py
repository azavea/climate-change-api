from django.test import TestCase

from climate_data.tests.mixins import ClimateDataSetupMixin
from indicators import indicators
from indicators.utils import merge_dicts


class IndicatorTests(ClimateDataSetupMixin, object):

    indicator_class = None    # Override this in subclass to set the indicator to test
    indicator_name = ''
    units = None
    time_aggregation = None
    extra_params = {}
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
        params = merge_dicts(self.extra_params,
                             {'units': self.units, 'time_aggregation': self.time_aggregation})
        indicator = self.indicator_class(self.city1, self.rcp85, parameters=params)
        data = indicator.calculate()
        self.assertEqual(data, self.test_indicator_rcp85_equals)

    def test_indicator_rcp45(self):
        params = merge_dicts(self.extra_params,
                             {'units': self.units, 'time_aggregation': self.time_aggregation})
        indicator = self.indicator_class(self.city1, self.rcp45, parameters=params)
        data = indicator.calculate()
        self.assertEqual(data, self.test_indicator_rcp45_equals)

    def test_indicator_no_data(self):
        params = merge_dicts(self.extra_params,
                             {'units': self.units, 'time_aggregation': self.time_aggregation})
        indicator = self.indicator_class(self.city2, self.rcp85, parameters=params)
        data = indicator.calculate()
        self.assertEqual(data, self.test_indicator_no_data_equals)

    def test_years_filter(self):
        params = merge_dicts(self.extra_params, {'units': self.units, 'years': '2001:2002',
                                                 'time_aggregation': self.time_aggregation})
        indicator = self.indicator_class(self.city1, self.rcp45, parameters=params)
        data = indicator.calculate()
        self.assertEqual(data, self.test_years_filter_equals)

    def test_models_filter(self):
        params = merge_dicts(self.extra_params, {'units': self.units, 'models': 'CCSM4',
                                                 'time_aggregation': self.time_aggregation})
        indicator = self.indicator_class(self.city1, self.rcp45, parameters=params)
        data = indicator.calculate()
        self.assertEqual(data, self.test_models_filter_equals)

    def test_unit_conversion_definitions(self):
        """Check sanity of unit conversion class attributes."""
        self.assertIn(self.indicator_class.default_units, self.indicator_class.available_units)


class TemperatureIndicatorTests(IndicatorTests):
    def test_unit_conversion(self):
        params = merge_dicts(self.extra_params,
                             {'units': 'F', 'time_aggregation': self.time_aggregation})
        indicator = self.indicator_class(self.city1, self.rcp85, parameters=params)
        data = indicator.calculate()
        self.assertEqual(data, self.test_units_fahrenheit_equals,
                         'Temperature should be converted to degrees F')


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


class CrossYearAverageHighTemperatureTestCase(TemperatureIndicatorTests, TestCase):
    indicator_class = indicators.AverageHighTemperatureArray
    indicator_name = 'average_high_temperature_array'
    time_aggregation = 'offset_yearly'
    units = 'K'
    test_indicator_rcp45_equals = {'2000-2001': {'max': 20.0, 'avg': 15.0, 'min': 10.0},
                                   '2001-2002': {'max': 10.0, 'avg': 10.0, 'min': 10.0},
                                   '2002-2003': {'avg': 10.0, 'max': 10.0, 'min': 10.0}}
    test_years_filter_equals = {'2001-2002': {'max': 10.0, 'avg': 10.0, 'min': 10.0},
                                '2002-2003': {'max': 10.0, 'avg': 10.0, 'min': 10.0}}
    test_models_filter_equals = {'2000-2001': {'avg': 10.0, 'max': 10.0, 'min': 10.0},
                                 '2001-2002': {'avg': 10.0, 'max': 10.0, 'min': 10.0},
                                 '2002-2003': {'avg': 10.0, 'max': 10.0, 'min': 10.0}}
    # offset_yearly aggregation reduces the number of data points from the fencepost effect, so
    # since there was only one data point for these we get nothing back.
    test_indicator_rcp85_equals = {}
    test_units_fahrenheit_equals = {}


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


class YearlyPercentileLowTemperatureTestCase(TemperatureIndicatorTests, TestCase):
    indicator_class = indicators.PercentileLowTemperature
    indicator_name = 'percentile_low_temperature'
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


class YearlyPercentileHighTemperatureTestCase(TemperatureIndicatorTests, TestCase):
    indicator_class = indicators.PercentileHighTemperature
    indicator_name = 'percentile_high_temperature'
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
    units = 'kg/m^2'
    test_indicator_rcp85_equals = {2000: {'avg': 3024000.0, 'min': 2592000, 'max': 3456000}}
    test_indicator_rcp45_equals = {2000: {'max': 1728000, 'avg': 1296000, 'min': 864000},
                                   2001: {'max': 1728000, 'avg': 1296000, 'min': 864000},
                                   2002: {'avg': 864000, 'max': 864000, 'min': 864000},
                                   2003: {'avg': 0.0, 'max': 0.0, 'min': 0.0}}
    test_years_filter_equals = {2001: {'max': 1728000, 'avg': 1296000, 'min': 864000},
                                2002: {'avg': 864000, 'max': 864000, 'min': 864000}}
    test_models_filter_equals = {2000: {'avg': 864000, 'max': 864000, 'min': 864000},
                                 2001: {'avg': 864000, 'max': 864000, 'min': 864000},
                                 2002: {'avg': 864000, 'max': 864000, 'min': 864000},
                                 2003: {'avg': 0.0, 'max': 0.0, 'min': 0.0}}


class YearlyPercentilePrecipitationTestCase(IndicatorTests, TestCase):
    indicator_class = indicators.PercentilePrecipitation
    indicator_name = 'percentile_precipitation'
    time_aggregation = 'yearly'
    units = 'kg/m^2'
    test_indicator_rcp85_equals = {2000: {'avg': 3024000.0, 'min': 2592000, 'max': 3456000}}
    test_indicator_rcp45_equals = {2000: {'max': 1728000, 'avg': 1296000, 'min': 864000},
                                   2001: {'max': 1728000, 'avg': 1296000, 'min': 864000},
                                   2002: {'avg': 864000, 'max': 864000, 'min': 864000},
                                   2003: {'avg': 0.0, 'max': 0.0, 'min': 0.0}}
    test_years_filter_equals = {2001: {'max': 1728000, 'avg': 1296000, 'min': 864000},
                                2002: {'avg': 864000, 'max': 864000, 'min': 864000}}
    test_models_filter_equals = {2000: {'avg': 864000, 'max': 864000, 'min': 864000},
                                 2001: {'avg': 864000, 'max': 864000, 'min': 864000},
                                 2002: {'avg': 864000, 'max': 864000, 'min': 864000},
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


class YearlyHeatWaveDurationIndexTestCase(IndicatorTests, TestCase):
    indicator_class = indicators.HeatWaveDurationIndex
    indicator_name = 'heat_wave_duration_index'
    time_aggregation = 'yearly'
    extra_params = {'historic_range': '1961'}
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


class YearlyHeatWaveIncidentsTestCase(IndicatorTests, TestCase):
    indicator_class = indicators.HeatWaveIncidents
    indicator_name = 'heat_wave_incidents'
    time_aggregation = 'yearly'
    extra_params = {'historic_range': '1961'}
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
    extra_params = {'percentile': '99', 'historic_range': '1961'}
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
    extra_params = {'percentile': '99', 'historic_range': '1961'}
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
    extra_params = {'percentile': '1', 'historic_range': '1961'}
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
    extra_params = {
        'basetemp': '42.5',
        'basetemp_units': 'K'
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


class YearlyDiurnalTemperatureRangeTestCase(IndicatorTests, TestCase):
    indicator_class = indicators.DiurnalTemperatureRange
    indicator_name = 'diurnal_temperature_range'
    time_aggregation = 'yearly'
    units = 'K'
    test_indicator_rcp85_equals = {2000: {'avg': 0.0, 'max': 0.0, 'min': 0.0}}
    test_indicator_rcp45_equals = {2000: {'max': 0.0, 'avg': 0.0, 'min': 0.0},
                                   2001: {'max': 0.0, 'avg': 0.0, 'min': 0.0},
                                   2002: {'avg': 0.0, 'max': 0.0, 'min': 0.0},
                                   2003: {'avg': 0.0, 'max': 0.0, 'min': 0.0}}
    test_years_filter_equals = {2001: {'max': 0.0, 'avg': 0.0, 'min': 0.0},
                                2002: {'avg': 0.0, 'max': 0.0, 'min': 0.0}}
    test_models_filter_equals = {2000: {'avg': 0.0, 'max': 0.0, 'min': 0.0},
                                 2001: {'avg': 0.0, 'max': 0.0, 'min': 0.0},
                                 2002: {'avg': 0.0, 'max': 0.0, 'min': 0.0},
                                 2003: {'avg': 0.0, 'max': 0.0, 'min': 0.0}}


class CrossYearlyHeatingDegreeDaysTestCase(IndicatorTests, TestCase):
    indicator_class = indicators.HeatingDegreeDays
    indicator_name = 'heating_degree_days'
    time_aggregation = 'offset_yearly'
    extra_params = {
        'basetemp': '42.5',
        'basetemp_units': 'K'
    }
    test_indicator_rcp85_equals = {}
    test_indicator_rcp45_equals = {'2000-2001': {'avg': 49.5, 'min': 40.5, 'max': 58.5},
                                   '2001-2002': {'avg': 58.5, 'min': 58.5, 'max': 58.5},
                                   '2002-2003': {'avg': 58.5, 'min': 58.5, 'max': 58.5}}
    # Years are filtered by the starting year, so years=2001,2002 gives data for 2001-2002
    # and 2002-2003
    test_years_filter_equals = {'2001-2002': {'avg': 58.5, 'min': 58.5, 'max': 58.5},
                                '2002-2003': {'avg': 58.5, 'min': 58.5, 'max': 58.5}}
    test_models_filter_equals = {'2000-2001': {'avg': 58.5, 'min': 58.5, 'max': 58.5},
                                 '2001-2002': {'avg': 58.5, 'min': 58.5, 'max': 58.5},
                                 '2002-2003': {'avg': 58.5, 'min': 58.5, 'max': 58.5}}


class YearlyCoolingDegreeDaysTestCase(IndicatorTests, TestCase):
    indicator_class = indicators.CoolingDegreeDays
    indicator_name = 'cooling_degree_days'
    time_aggregation = 'yearly'
    extra_params = {
        'basetemp': '-265.85',  # 7.3K
        'basetemp_units': 'C'
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


class CrossYearlyAccumulatedFreezingDegreeDaysTestCase(IndicatorTests, TestCase):
    indicator_class = indicators.AccumulatedFreezingDegreeDays
    indicator_name = 'accumulated_freezing_degree_days'
    time_aggregation = 'offset_yearly'
    test_indicator_rcp85_equals = {}
    test_indicator_rcp45_equals = {'2000-2001': {'avg': 464.66999999999996, 'min': 455.67,
                                                 'max': 473.66999999999996},
                                   '2001-2002': {'avg': 473.66999999999996,
                                                 'max': 473.66999999999996,
                                                 'min': 473.66999999999996},
                                   '2002-2003': {'avg': 473.66999999999996,
                                                 'max': 473.66999999999996,
                                                 'min': 473.66999999999996}}
    # Years are filtered by the starting year, so years=2001,2002 gives data for 2001-2002
    # and 2002-2003
    test_years_filter_equals = {'2001-2002': {'avg': 473.66999999999996, 'max': 473.66999999999996,
                                              'min': 473.66999999999996},
                                '2002-2003': {'avg': 473.66999999999996,
                                              'max': 473.66999999999996,
                                              'min': 473.66999999999996}}
    test_models_filter_equals = {'2000-2001': {'avg': 473.66999999999996, 'max': 473.66999999999996,
                                               'min': 473.66999999999996},
                                 '2001-2002': {'avg': 473.66999999999996, 'max': 473.66999999999996,
                                               'min': 473.66999999999996},
                                 '2002-2003': {'avg': 473.66999999999996, 'max': 473.66999999999996,
                                               'min': 473.66999999999996}}


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
    units = 'kg/m^2'
    test_indicator_rcp85_equals = {'2000-01': {'avg': 3024000, 'min': 2592000, 'max': 3456000}}
    test_indicator_rcp45_equals = {'2000-01': {'max': 1728000, 'avg': 1296000.0, 'min': 864000},
                                   '2001-01': {'max': 1728000, 'avg': 1296000.0, 'min': 864000},
                                   '2002-01': {'avg': 864000, 'max': 864000, 'min': 864000},
                                   '2003-01': {'avg': 0.0, 'max': 0.0, 'min': 0.0}}
    test_years_filter_equals = {'2001-01': {'max': 1728000, 'avg': 1296000.0, 'min': 864000},
                                '2002-01': {'avg': 864000, 'max': 864000, 'min': 864000}}
    test_models_filter_equals = {'2000-01': {'avg': 864000, 'max': 864000, 'min': 864000},
                                 '2001-01': {'avg': 864000, 'max': 864000, 'min': 864000},
                                 '2002-01': {'avg': 864000, 'max': 864000, 'min': 864000},
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
    extra_params = {'percentile': '99', 'historic_range': '1961'}
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
    extra_params = {'percentile': '99', 'historic_range': '1961'}
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
    extra_params = {'percentile': '1', 'historic_range': '1961'}
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
    units = 'F'
    extra_params = {
        'basetemp': '-384.07'
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
    units = 'C'
    extra_params = {
        'basetemp': '-273.15',
        'basetemp_units': 'C'
    }
    test_indicator_rcp85_equals = {'2000-01': {'max': 40.0, 'avg': 35.0, 'min': 30.0}}
    test_indicator_rcp45_equals = {'2000-01': {'max': 20.0, 'avg': 15.0, 'min': 10.0},
                                   '2003-01': {'max': 10.0, 'avg': 10.0, 'min': 10.0},
                                   '2001-01': {'max': 20.0, 'avg': 15.0, 'min': 10.0},
                                   '2002-01': {'max': 10.0, 'avg': 10.0, 'min': 10.0}}
    test_years_filter_equals = {'2001-01': {'max': 20.0, 'avg': 15.0, 'min': 10.0},
                                '2002-01': {'max': 10.0, 'avg': 10.0, 'min': 10.0}}
    test_models_filter_equals = {'2000-01': {'max': 10.0, 'avg': 10.0, 'min': 10.0},
                                 '2003-01': {'max': 10.0, 'avg': 10.0, 'min': 10.0},
                                 '2001-01': {'max': 10.0, 'avg': 10.0, 'min': 10.0},
                                 '2002-01': {'max': 10.0, 'avg': 10.0, 'min': 10.0}}


class MonthlyPrecipitationThresholdTestcase(IndicatorTests, TestCase):
    indicator_class = indicators.PrecipitationThreshold
    indicator_name = 'precipitation_threshold'
    time_aggregation = 'monthly'
    extra_params = {'threshold': .5, 'threshold_comparator': 'lt', 'threshold_units': 'in'}
    test_indicator_rcp85_equals = {'2000-01': {'avg': 0.0, 'min': 0.0, 'max': 0.0}}
    test_indicator_rcp45_equals = {'2000-01': {'max': 1.0, 'avg': 0.5, 'min': 0.0},
                                   '2001-01': {'max': 1.0, 'avg': 0.5, 'min': 0.0},
                                   '2002-01': {'avg': 1.0, 'max': 1.0, 'min': 1.0},
                                   '2003-01': {'avg': 1.0, 'max': 1.0, 'min': 1.0}}
    test_years_filter_equals = {'2001-01': {'max': 1.0, 'avg': 0.5, 'min': 0.0},
                                '2002-01': {'avg': 1.0, 'max': 1.0, 'min': 1.0}}
    test_models_filter_equals = {'2000-01': {'avg': 1.0, 'max': 1.0, 'min': 1.0},
                                 '2001-01': {'avg': 1.0, 'max': 1.0, 'min': 1.0},
                                 '2002-01': {'avg': 1.0, 'max': 1.0, 'min': 1.0},
                                 '2003-01': {'avg': 1.0, 'max': 1.0, 'min': 1.0}}
