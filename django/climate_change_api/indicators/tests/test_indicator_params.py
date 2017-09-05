from django.core.exceptions import ValidationError
from django.test import TestCase

from climate_data.tests.mixins import ClimateDataSetupMixin
from climate_data.tests.factories import HistoricDateRangeFactory
from indicators import indicators
from indicators.params import (IndicatorParam, IndicatorParams, PercentileIndicatorParams,
                               HeatWaveIndicatorParams)
from indicators.utils import merge_dicts
from indicators.validators import ChoicesValidator


available_units_validator = ChoicesValidator(['K', 'C', 'F'])


class IndicatorParamTestCase(TestCase):

    def test_sets_default(self):
        param = IndicatorParam('units', default='F')
        param.set_value('K')
        self.assertEqual(param.value, 'K')

        param = IndicatorParam('units', default='F')
        param.set_value(None)
        self.assertEqual(param.value, 'F')

    def test_required_with_default(self):
        param = IndicatorParam('units', required=True, default='F')
        param.set_value(None)
        self.assertEqual(param.value, 'F')

    def test_required_no_default(self):
        param = IndicatorParam('units', required=True, default=None)
        with self.assertRaises(ValidationError):
            param.set_value(None)

    def test_blank_validators(self):
        """Set validators to empty array if None provided."""
        param = IndicatorParam('units', validators=None)
        self.assertEqual(param.validators, [])
        param = IndicatorParam('units')
        self.assertEqual(param.validators, [])


class IndicatorParamsTestCase(TestCase):

    def setUp(self):
        self.default_parameters = {}
        self.params_class_kwargs = {}
        self.default_units = 'F'
        self.available_units = ('F', 'C', 'K',)
        self.valid_aggregations = ('yearly', 'monthly',)
        self.params_class = IndicatorParams

    def _get_params_class(self):
        return self.params_class(self.default_units, self.available_units, self.valid_aggregations,
                                 **self.params_class_kwargs)

    def test_validate_valid_only_expected_params(self):
        """Ensure indicator_params sets values for each of the base params."""
        parameters = merge_dicts(self.default_parameters,
                                 {'models': 'CCSM4', 'years': '2050:2060', 'units': 'K',
                                  'agg': 'avg', 'time_aggregation': 'monthly'})
        indicator_params = self._get_params_class()
        indicator_params.validate(parameters)
        self.assertEqual(indicator_params.models.value, ['CCSM4'])
        self.assertEqual(indicator_params.years.value, ['2050:2060'])
        self.assertEqual(indicator_params.units.value, 'K')
        self.assertEqual(indicator_params.agg.value, ['avg'])
        self.assertEqual(indicator_params.time_aggregation.value, 'monthly')

    def test_validate_valid_some_unused_params(self):
        """Ensure indicator_params properly ignores params that aren't defined."""
        parameters = merge_dicts(self.default_parameters,
                                 {'doesnotexist': 'true',
                                  'years': '2050:2060',
                                  'units': 'K',
                                  'agg': 'avg'})
        indicator_params = self._get_params_class()
        indicator_params.validate(parameters)
        with self.assertRaises(AttributeError):
            indicator_params.doesnotexist

    def test_validate_valid_optional_defaults(self):
        """Ensure indicator_params properly sets defaults on base params.

        Force units to have default value by overriding IndicatorParams.
        """
        parameters_sets = [
            {'models': None, 'years': None, 'units': None, 'agg': None, 'time_aggregation': None},
            {}
        ]
        for parameters in parameters_sets:
            p = merge_dicts(self.default_parameters, parameters)
            indicator_params = self._get_params_class()
            indicator_params.validate(p)
            self.assertEqual(indicator_params.years.value, [])
            self.assertEqual(indicator_params.models.value, [])
            self.assertEqual(indicator_params.agg.serialized_value, indicator_params.agg.default)
            self.assertEqual(indicator_params.units.serialized_value, self.default_units)
            self.assertEqual(indicator_params.time_aggregation.serialized_value,
                             indicator_params.time_aggregation.default)


class IndicatorParamsBeforeSerializerTestCase(ClimateDataSetupMixin, TestCase):

    def setUp(self):
        super(IndicatorParamsBeforeSerializerTestCase, self).setUp()

    def test_parsing_single_agg_string_input(self):
        """Test a string input of single aggregation method."""
        self._test_parsing_agg_string_input('99th')

    def test_parsing_multi_agg_string_input(self):
        """Test a comma-separated string input of multi aggregation methods."""
        self._test_parsing_agg_string_input('avg,99th,stdev')

    def _test_parsing_agg_string_input(self, agg_input):
        """Ensure CSV string input for aggregation param parsed into list before serialization."""
        parameters = merge_dicts({}, {'agg': agg_input})
        # test string parsing on an arbitrary indicator
        indicator = indicators.TotalPrecipitation(self.city1, self.rcp45, parameters=parameters)
        results = indicator.calculate()

        split_input = agg_input.split(',')
        for idx in results:
            # only need to check keys from one result since all results will have identical keys
            return self.assertTrue(set(split_input) == set(results[idx].keys()),
                                   msg="Agg inputs improperly formatted or parsed")


class PercentileIndicatorParamsTestCase(IndicatorParamsTestCase):

    def setUp(self):
        super(PercentileIndicatorParamsTestCase, self).setUp()
        self.params_class = PercentileIndicatorParams
        self.params_class_kwargs = {'percentile': 99}

    def test_validate_percentile_default(self):
        """Use a default value if required param is missing."""
        parameters = {'percentile': None}
        indicator_params = self._get_params_class()
        indicator_params.validate(parameters)
        self.assertEqual(indicator_params.percentile.value, 99)

    def test_validate_percentile_out_of_bounds(self):
        """Raise ValidationError if percentile outside range [0-100]."""
        parameters = merge_dicts(self.default_parameters, {'percentile': '-1'})
        indicator_params = self._get_params_class()
        with self.assertRaises(ValidationError):
            indicator_params.validate(parameters)

        parameters = merge_dicts(self.default_parameters, {'percentile': '101'})
        indicator_params = self._get_params_class()
        with self.assertRaises(ValidationError):
            indicator_params.validate(parameters)


class HeatWaveIndicatorParamsTestCase(IndicatorParamsTestCase):

        def setUp(self):
            super(HeatWaveIndicatorParamsTestCase, self).setUp()
            self.range1 = HistoricDateRangeFactory(start_year=1951, end_year=1980)
            self.range2 = HistoricDateRangeFactory(start_year=1961, end_year=1990)
            self.params_class = HeatWaveIndicatorParams

        def test_default_to_most_recent_historic_range(self):
            indicator_params = self._get_params_class()
            self.assertEqual(indicator_params.historic_range.default, str(self.range2.pk))

        def test_validate_range_outside_of_choices(self):
            parameters = merge_dicts(self.default_parameters, {'historic_range': '2010'})
            indicator_params = self._get_params_class()
            with self.assertRaises(ValidationError):
                indicator_params.validate(parameters)
