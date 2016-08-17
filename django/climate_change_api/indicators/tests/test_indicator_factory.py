from django.test import TestCase

from indicators import indicator_factory


class IndicatorFactoryTestCase(TestCase):

    def test_indicator_factory_returns_class(self):
        IndicatorClass = indicator_factory('yearly_average_max_temperature')
        self.assertEqual(IndicatorClass.__name__, 'YearlyAverageMaxTemperature')

    def test_indicator_factory_invalid_argument(self):
        IndicatorClass = indicator_factory('does_not_exist')
        self.assertIsNone(IndicatorClass)
