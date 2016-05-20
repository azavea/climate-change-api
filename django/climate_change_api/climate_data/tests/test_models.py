from django.test import TestCase

from climate_data.tests.factories import ClimateModelFactory


class ModelsTestCase(TestCase):

    def test_climate_model_str_returns_name(self):
        """ A contrived example, but demonstrates use of factory_boy """

        cm = ClimateModelFactory(name='ukmet')
        self.assertEqual(str(cm), 'ukmet')
