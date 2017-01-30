
from django.test import TestCase

from indicators.serializers import IndicatorSerializer


class IndicatorSerializerTestCase(TestCase):
    def setUp(self):
        self.serializer = IndicatorSerializer()
        self.data = {
            '2010': [1, 2, 3, 3, 3, 5, 5, 8, 9, 10],
        }

    def test_serializer_aggregation(self):
        """Ensure all available aggregation types return the correct values."""
        aggregations = ('avg', 'max', 'min', 'median', 'stddev', '95th', '99th',)
        results = self.serializer.to_representation(self.data, aggregations=aggregations)
        self.assertEqual(results, {
            '2010': {
                '95th': 9.5499999999999989,
                '99th': 9.9100000000000001,
                'avg': 4.9,
                'max': 10,
                'median': 4.0,
                'min': 1,
                'stddev': 2.947880594596735,
            }
        })

    def test_serializer_aggregation_default(self):
        """Ensure that the default returns at least one aggregation type."""
        results = self.serializer.to_representation(self.data)
        self.assertGreater(len(list(results['2010'].keys())), 0)

    def test_serializer_aggregation_ignores_bad_input(self):
        aggregations = ('avg', 'nope', '', None, 23, {})
        results = self.serializer.to_representation(self.data, aggregations=aggregations)
        self.assertEqual(len(list(results['2010'].keys())), 1)

    def test_serializer_percentiles(self):
        aggregations = ('1th', '5th', '95th', '99th',)
        results = self.serializer.to_representation(self.data, aggregations=aggregations)
        self.assertEqual(results, {
            '2010': {
                '1th': 1.0900000000000001,
                '5th': 1.4500000000000002,
                '95th': 9.5499999999999989,
                '99th': 9.9100000000000001
            }
        })
