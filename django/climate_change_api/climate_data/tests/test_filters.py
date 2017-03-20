from django.test import TestCase


from climate_data.filters import ClimateDataFilterSet
from climate_data.tests.mixins import ClimateDataSetupMixin
from climate_data.models import ClimateData


class ClimateDataFilterSetTestCase(ClimateDataSetupMixin, TestCase):
    """Test filtering climate datasets.

    TODO: Test the response querysets, not just their length.
    """

    def setUp(self):

        super(ClimateDataFilterSetTestCase, self).setUp()
        self.queryset = (ClimateData.objects.filter(map_cell__city=self.city1)
                                            .filter(data_source__scenario=self.rcp45))

    def test_models_filter(self):

        self.assertEqual(self.queryset.count(), 6)

        query_params = {'models': self.model1.name}
        data_filter = ClimateDataFilterSet(query_params, self.queryset)
        self.assertEqual(data_filter.qs.count(), 4)

        query_params = {'models': self.model1.name + ',,doesntexist'}
        data_filter = ClimateDataFilterSet(query_params, self.queryset)
        self.assertEqual(data_filter.qs.count(), 4)

        query_params = {'models': ''}
        data_filter = ClimateDataFilterSet(query_params, self.queryset)
        self.assertEqual(data_filter.qs.count(), 6)

    def test_years_filter(self):

        self.assertEqual(self.queryset.count(), 6)

        query_params = {'years': '2001'}
        data_filter = ClimateDataFilterSet(query_params, self.queryset)
        self.assertEqual(data_filter.qs.count(), 2)

        query_params = {'years': '2001,2002'}
        data_filter = ClimateDataFilterSet(query_params, self.queryset)
        self.assertEqual(data_filter.qs.count(), 3)

        query_params = {'years': '2000:2001,2002'}
        data_filter = ClimateDataFilterSet(query_params, self.queryset)
        self.assertEqual(data_filter.qs.count(), 5)

        query_params = {'years': '2002:2003'}
        data_filter = ClimateDataFilterSet(query_params, self.queryset)
        self.assertEqual(data_filter.qs.count(), 2)
