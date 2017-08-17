from django.test import TestCase
from indicators import indicator_factory


class IndicatorFactoryTestCase(TestCase):

    def test_indicator_factory_returns_class(self):
        IndicatorClass = indicator_factory('average_high_temperature')
        self.assertEqual(IndicatorClass.__name__, 'AverageHighTemperature')

    def test_indicator_factory_invalid_argument(self):
        IndicatorClass = indicator_factory('does_not_exist')
        self.assertIsNone(IndicatorClass)

    def test_indicator_factory_yearly_lookup(self):
        IndicatorClass = indicator_factory('yearly_dry_spells')
        self.assertEqual(IndicatorClass.__name__, 'DrySpells')
