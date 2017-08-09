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

    def test_indicator_factory_yearly_lookup(self):
        IndicatorClass = indicator_factory('yearly_dry_spells')
        if settings.FEATURE_FLAGS['array_data']:
            self.assertEqual(IndicatorClass.__name__, 'DrySpellsArray')
        else:
            # TODO: remove this block and feature flag test with task #567
            self.assertEqual(IndicatorClass.__name__, 'DrySpells')

    def test_indicator_factory_yearly_lookup_explicit_array(self):
        # TODO: remove this test with task #567
        IndicatorClass = indicator_factory('yearly_dry_spells_array')
        self.assertEqual(IndicatorClass.__name__, 'DrySpellsArray')

    def test_indicator_factory_explicit_array_lookup(self):
        # TODO: remove this test with task #567
        IndicatorClass = indicator_factory('average_high_temperature_array')
        self.assertEqual(IndicatorClass.__name__, 'AverageHighTemperatureArray')
