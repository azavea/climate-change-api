from django.test import TestCase

from indicators import list_available_indicators

from climate_data.tests.factories import HistoricDateRangeFactory


class AvailableIndicatorListTestCase(TestCase):

    def setUp(self):
        # Having at least 1 HistoricDateRange is necessary for the params to initialize
        super(AvailableIndicatorListTestCase, self).setUp()
        HistoricDateRangeFactory(start_year=1951, end_year=1980)

    def test_indicator_detection_count(self):
        indicators = list_available_indicators()
        self.assertEqual(len(indicators), 23)
