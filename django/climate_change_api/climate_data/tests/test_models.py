from django.test import TestCase

from climate_data.tests.factories import ClimateDatasetFactory, ClimateModelFactory, ScenarioFactory
from climate_data.tests.mixins import ClimateDataSetupMixin
from climate_data.models import (City,
                                 ClimateDataset,
                                 ClimateDataCell,
                                 ClimateDataSource)


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
            self.city1.get_map_cell(dataset)

    def test_get_map_cell_raises_correct_exception_class(self):
        dataset = ClimateDataset.objects.create(name='DOESNOTEXIST')
        with self.assertRaises(ClimateDataCell.DoesNotExist):
            self.city1.get_map_cell(dataset)


class ClimateDatasetTestCase(TestCase):

    def setUp(self):
        # Dataset/model objects actually created by migrations
        self.loca = ClimateDatasetFactory(name='LOCA')
        self.gddp = ClimateDatasetFactory(name='NEX-GDDP')

        self.loca_model = ClimateModelFactory(name='ACCESS1-3')
        self.both_model = ClimateModelFactory(name='ACCESS1-0')

        self.loca.models.add(self.both_model)
        self.loca.models.add(self.loca_model)
        self.gddp.models.add(self.both_model)

    def test_has_model(self):
        self.assertTrue(self.loca.has_model(self.both_model.name))
        self.assertTrue(self.gddp.has_model(self.both_model.name))
        self.assertTrue(self.loca.has_model(self.loca_model.name))
        self.assertFalse(self.gddp.has_model(self.loca_model.name))


class ClimateDataSourceTestCase(TestCase):

    def setUp(self):
        # Dataset/model objects actually created by migrations
        self.loca = ClimateDatasetFactory(name='LOCA')
        self.loca_model = ClimateModelFactory(name='ACCESS1-3')
        self.gddp_model = ClimateModelFactory(name='BNU-ESM')
        self.scenario = ScenarioFactory(name='RCP85')

    def test_save_check_datset_models(self):
        ClimateDataSource.objects.create(scenario=self.scenario,
                                         dataset=self.loca,
                                         model=self.loca_model,
                                         year=2000)
        with self.assertRaises(ValueError):
            ClimateDataSource.objects.create(scenario=self.scenario,
                                             dataset=self.loca,
                                             model=self.gddp_model,
                                             year=2000)
