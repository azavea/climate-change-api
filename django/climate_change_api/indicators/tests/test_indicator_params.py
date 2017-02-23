from django.core.exceptions import ValidationError
from django.test import TestCase

from climate_data.tests.mixins import ClimateDataSetupMixin
from indicators import indicators
from indicators.params import IndicatorParam, IndicatorParams, PercentileIndicatorParams
from indicators.utils import merge_dicts
from indicators.validators import ChoicesValidator


available_units_validator = ChoicesValidator(['K', 'C', 'F'])


class IndicatorParamTestCase(TestCase):

    def test_sets_default(self):
        param = IndicatorParam('units', default='F')
        param.validate('K')
        self.assertEqual(param.value, 'K')

        param = IndicatorParam('units', default='F')
        param.validate(None)
        self.assertEqual(param.value, 'F')

    def test_required_with_default(self):
        param = IndicatorParam('units', required=True, default='F')
        param.validate(None)
        self.assertEqual(param.value, 'F')

    def test_required_no_default(self):
        param = IndicatorParam('units', required=True, default=None)
        with self.assertRaises(ValidationError):
            param.validate(None)

    def test_blank_validators(self):
        """ should set validators to empty array if None provided """
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
        """ it should ensure indicator_params sets values for each of the base params """
        parameters = merge_dicts(self.default_parameters,
                                 {'models': 'CCSM4', 'years': '2050:2060', 'units': 'K',
                                  'agg': 'avg', 'time_aggregation': 'monthly'})
        indicator_params = self._get_params_class()
        indicator_params.validate(parameters)
        self.assertEqual(indicator_params.models.value, 'CCSM4')
        self.assertEqual(indicator_params.years.value, '2050:2060')
        self.assertEqual(indicator_params.units.value, 'K')
        self.assertEqual(indicator_params.agg.value, 'avg')
        self.assertEqual(indicator_params.time_aggregation.value, 'monthly')

    def test_validate_valid_some_unused_params(self):
        """ it should ensure indicator_params properly ignores params that aren't defined """
        parameters = merge_dicts(self.default_parameters,
                                 {'doesnotexist': 'true', 'years': '2050:2060', 'units': 'K', 'agg': 'avg'})
        indicator_params = self._get_params_class()
        indicator_params.validate(parameters)
        with self.assertRaises(AttributeError):
            value = indicator_params.doesnotexist

    def test_validate_valid_optional_defaults(self):
        """ it should ensure indicator_params properly sets defaults on base params

        Force units to have default value by overriding IndicatorParams

        """
        parameters_sets = [
            {'models': None, 'years': None, 'units': None, 'agg': None, 'time_aggregation': None},
            {}
        ]
        for parameters in parameters_sets:
            p = merge_dicts(self.default_parameters, parameters)
            indicator_params = self._get_params_class()
            indicator_params.validate(p)
            self.assertIsNone(indicator_params.years.value)
            self.assertIsNone(indicator_params.models.value)
            self.assertEqual(indicator_params.agg.value, indicator_params.agg.default)
            self.assertEqual(indicator_params.units.value, self.default_units)
            self.assertEqual(indicator_params.time_aggregation.value,
                             indicator_params.time_aggregation.default)


class IndicatorParamsBeforeSerializerTestCase(ClimateDataSetupMixin, TestCase):

    def setUp(self):
        super(IndicatorParamsBeforeSerializerTestCase, self).setUp()

    def test_parsing_single_agg_string_input(self):
        """ tests a string input of single aggregation method """

        self._test_parsing_agg_string_input('99th')

    def test_parsing_multi_agg_string_input(self):
        """ tests a comma-separated string input of multi aggregation methods """

        self._test_parsing_agg_string_input('avg,99th,stdev')

    def _test_parsing_agg_string_input(self, agg_input):
        """ method should ensure a csv string input for the aggregation param gets
            parsed into a list before serialization
        """
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
        """ It should use a default value if required param is missing """
        parameters = {'percentile': None}
        indicator_params = self._get_params_class()
        indicator_params.validate(parameters)
        self.assertEqual(indicator_params.percentile.value, 99)

    def test_validate_percentile_out_of_bounds(self):
        """ It should raise ValidationError if percentile outside range [0-100] """
        parameters = merge_dicts(self.default_parameters, {'percentile': '-1'})
        indicator_params = self._get_params_class()
        with self.assertRaises(ValidationError):
            indicator_params.validate(parameters)

        parameters = merge_dicts(self.default_parameters, {'percentile': '101'})
        indicator_params = self._get_params_class()
        with self.assertRaises(ValidationError):
            indicator_params.validate(parameters)
