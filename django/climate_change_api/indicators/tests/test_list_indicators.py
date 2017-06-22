import inspect
import sys

from django.test import TestCase

from indicators import list_available_indicators

from climate_data.tests.factories import HistoricDateRangeFactory


class AvailableIndicatorListTestCase(TestCase):

    def setUp(self):
        # Having at least 1 HistoricDateRange is necessary for the params to initialize
        super(AvailableIndicatorListTestCase, self).setUp()
        HistoricDateRangeFactory(start_year=1951, end_year=1980)

    def test_indicator_list_ignores_classes_not_defined_in_module(self):
        indicators = list_available_indicators()
        class_members = inspect.getmembers(sys.modules['indicators.indicators'], inspect.isclass)
        indicators_via_introspection = [m[1] for m in class_members
                                        if m[1].__module__ == 'indicators.indicators']
        self.assertEqual(len(indicators), len(indicators_via_introspection))
