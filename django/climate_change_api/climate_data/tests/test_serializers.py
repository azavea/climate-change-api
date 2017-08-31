from django.test import TestCase

from climate_data.models import ClimateDataYear
from climate_data.tests.mixins import ClimateDataSetupMixin
from climate_data.serializers import ClimateCityScenarioDataSerializer


class ClimateCityScenarioDataSerializerTestCase(ClimateDataSetupMixin, TestCase):
    """Test that this serializer properly generates the output python object we expect."""

    def setUp(self):

        super(ClimateCityScenarioDataSerializerTestCase, self).setUp()
        self.VARIABLE_CHOICES = ClimateDataYear.VARIABLE_CHOICES
        self.queryset = (ClimateDataYear.objects.filter(map_cell__city_set__city=self.city1)
                                                .filter(data_source__scenario=self.rcp45))

    def assert_serializer_data_valid(self, data, variable_list, value_to_check):
        """Helper to test the serialized python object.

        Should validate the format:
        {
            year: {
                'variable': [day1, day2, ..., day366],
                ...
            }
        }
        """
        self.assertIn(2000, data)
        self.assertIn(2001, data)
        year_dict = data[2000]
        for variable in variable_list:
            self.assertIn(variable, year_dict)
            self.assertEqual(year_dict[variable][0], value_to_check)
            self.assertEqual(len(year_dict[variable]), 366)

    def test_data_aggregation(self):
        """Get all data we've created and ensure it matches the output we expect.

        Also tests the default context, which is that all variables are returned and
        that avg is the default aggregation.
        """
        serializer = ClimateCityScenarioDataSerializer(self.queryset)
        self.assert_serializer_data_valid(serializer.data, self.VARIABLE_CHOICES, 15.0)

    def test_limit_output_variables(self):
        """Check output object only contains variables passed in via the context."""
        variable_list = list(self.VARIABLE_CHOICES)
        skip_var = variable_list.pop()
        context = {'variables': variable_list}
        serializer = ClimateCityScenarioDataSerializer(self.queryset, context=context)
        self.assertNotIn(skip_var, serializer.data[2000])
        self.assertNotIn(skip_var, serializer.data[2001])
        self.assert_serializer_data_valid(serializer.data, variable_list, 15.0)

    def test_min_aggregation(self):
        context = {'aggregation': 'min'}
        serializer = ClimateCityScenarioDataSerializer(self.queryset, context=context)
        self.assert_serializer_data_valid(serializer.data, self.VARIABLE_CHOICES, 10.0)

    def test_max_aggregation(self):
        context = {'aggregation': 'max'}
        serializer = ClimateCityScenarioDataSerializer(self.queryset, context=context)
        self.assert_serializer_data_valid(serializer.data, self.VARIABLE_CHOICES, 20.0)

    def test_limit_models(self):
        """Check serializer computes the average using only the filtered models."""
        queryset = self.queryset.filter(data_source__model=self.model1)
        serializer = ClimateCityScenarioDataSerializer(queryset)
        self.assert_serializer_data_valid(serializer.data, self.VARIABLE_CHOICES, 10.0)

        queryset = self.queryset.filter(data_source__model=self.model2)
        serializer = ClimateCityScenarioDataSerializer(queryset)
        self.assert_serializer_data_valid(serializer.data, self.VARIABLE_CHOICES, 20.0)
