import inspect
import sys

from django.test import TestCase

from indicators import list_available_indicators


class AvailableIndicatorListTestCase(TestCase):

    def test_indicator_list_ignores_classes_not_defined_in_module(self):
        indicators = list_available_indicators()
        class_members = inspect.getmembers(sys.modules['indicators.indicators'], inspect.isclass)
        indicators_via_introspection = [m[1] for m in class_members
                                        if m[1].__module__ == 'indicators.indicators']
        self.assertEqual(len(indicators), len(indicators_via_introspection))
