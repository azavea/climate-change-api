from django.conf import settings
from django.test import TestCase

from indicators import indicator_factory


class IndicatorFactoryTestCase(TestCase):

    def test_indicator_factory_returns_class(self):
        IndicatorClass = indicator_factory('average_high_temperature')
        if settings.FEATURE_FLAGS['array_data']:
            self.assertEqual(IndicatorClass.__name__, 'AverageHighTemperatureArray')
        else:
            # TODO: remove this block and feature flag test with task #567
            self.assertEqual(IndicatorClass.__name__, 'AverageHighTemperature')

    def test_indicator_factory_invalid_argument(self):
        IndicatorClass = indicator_factory('does_not_exist')
        self.assertIsNone(IndicatorClass)
