from django.test import TestCase

from climate_data.models import ClimateData
from climate_data.tests.factories import ClimateModelFactory, generate_climate_data


class ModelsTestCase(TestCase):

    def test_climate_model_str_returns_name(self):
        """ A contrived example, but demonstrates use of factory_boy """

        cm = ClimateModelFactory(name='ukmet')
        self.assertEqual(str(cm), 'ukmet')


class DataTestCase(TestCase):
    """ Also a contrived example, demonstrates use of generate_climate_data() """

    def test_data_exists(self):
        self.assertEqual(ClimateData.objects.all().count(), 0)
        generate_climate_data()
        self.assertEqual(ClimateData.objects.all().count(), 295)
