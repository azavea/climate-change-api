from django.test import TestCase

from climate_data.tests.mixins import ClimateDataSetupMixin
from climate_data.models import City, ClimateDataCell


class ModelsTestCase(ClimateDataSetupMixin, TestCase):

    def test_delete_data_cell_does_not_delete_associated_city(self):
        self.assertEqual(City.objects.count(), 2)
        self.assertEqual(self.city1, City.objects.get(id=self.city1.id))
        self.assertEqual(self.city1.map_cell, self.mapcell)
        count = ClimateDataCell.objects.count()

        self.mapcell.delete()
        self.assertIsNone(self.city1.map_cell.id)
        self.assertEqual(ClimateDataCell.objects.count(), count - 1)
