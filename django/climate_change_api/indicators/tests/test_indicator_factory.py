from django.test import TestCase
from indicators import indicator_factory


class IndicatorFactoryTestCase(TestCase):

    def test_indicator_factory_returns_class(self):
        IndicatorClass = indicator_factory('average_high_temperature')
        self.assertEqual(IndicatorClass.__name__, 'AverageHighTemperatureArray')

    def test_indicator_factory_invalid_argument(self):
        IndicatorClass = indicator_factory('does_not_exist')
        self.assertIsNone(IndicatorClass)

    def test_indicator_factory_yearly_lookup(self):
        IndicatorClass = indicator_factory('yearly_dry_spells')
        self.assertEqual(IndicatorClass.__name__, 'DrySpellsArray')

    def test_indicator_factory_yearly_lookup_explicit_array(self):
        # TODO: remove this test with task #567
        IndicatorClass = indicator_factory('yearly_dry_spells_array')
        self.assertEqual(IndicatorClass.__name__, 'DrySpellsArray')

    def test_indicator_factory_explicit_array_lookup(self):
        # TODO: remove this test with task #567
        IndicatorClass = indicator_factory('average_high_temperature_array')
        self.assertEqual(IndicatorClass.__name__, 'AverageHighTemperatureArray')
