from django.test import TestCase

from climate_data.tests.mixins import ClimateDataSetupMixin
from climate_data.models import City, ClimateDataset, ClimateDataCell, ClimateDataCityCell


class ModelsTestCase(ClimateDataSetupMixin, TestCase):

    def test_delete_data_cell_does_not_delete_associated_city(self):
        self.assertEqual(City.objects.count(), 2)
        self.assertEqual(self.city1, City.objects.get(id=self.city1.id))
        self.assertEqual(self.city1.map_cell_set.get().map_cell, self.mapcell)
        count = ClimateDataCell.objects.count()

        self.mapcell.delete()
        self.assertFalse(self.city1.map_cell_set.exists())
        self.assertEqual(ClimateDataCell.objects.count(), count - 1)

class CityTestCase(ClimateDataSetupMixin, TestCase):

    def test_get_map_cell(self):
        dataset = ClimateDataset.objects.get(name='NEX-GDDP')
        map_cell = self.city1.get_map_cell(dataset)
        self.assertEqual(map_cell.id, self.mapcell.id)

    def test_get_map_cell_single_db_query(self):
        dataset = ClimateDataset.objects.get(name='NEX-GDDP')
        with self.assertNumQueries(1):
            map_cell = self.city1.get_map_cell(dataset)

    def test_get_map_cell_raises_correct_exception_class(self):
        dataset = ClimateDataset.objects.create(name='DOESNOTEXIST')
        with self.assertRaises(ClimateDataCell.DoesNotExist):
            map_cell = self.city1.get_map_cell(dataset)

