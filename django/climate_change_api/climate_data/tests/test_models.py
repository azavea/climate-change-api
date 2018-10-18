from decimal import Decimal

from django.test import TestCase

from climate_data.tests.factories import ClimateDatasetFactory, ClimateModelFactory, ScenarioFactory
from climate_data.tests.mixins import ClimateDataSetupMixin
from climate_data.models import (
    City,
    ClimateDataset,
    ClimateDataCell,
    ClimateDataSource,
    ClimateDataYear,
    ClimateModel,
    Scenario,
)


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


class ClimateDataCellManagerTestCase(TestCase):

    def setUp(self):
        self.nex_gddp = ClimateDataset.objects.get(name=ClimateDataset.Datasets.NEX_GDDP)
        self.loca = ClimateDataset.objects.get(name=ClimateDataset.Datasets.LOCA)
        self.model = ClimateModel.objects.get(name='CCSM4')
        self.scenario = Scenario.objects.create(name='RCP85')
        self.data_source = ClimateDataSource.objects.create(dataset=self.nex_gddp,
                                                            model=self.model,
                                                            scenario=self.scenario,
                                                            year=2050,
                                                            import_completed=True)

    def _make_data_for_map_cell(self, map_cell):
        ClimateDataYear.objects.create(data_source=self.data_source,
                                       map_cell=map_cell,
                                       tasmax=[], tasmin=[], pr=[])

    def test_map_cell_for_lat_lon(self):
        target_map_cell = ClimateDataCell.objects.create(lat=Decimal(0.0), lon=Decimal(0.0))
        self._make_data_for_map_cell(target_map_cell)
        map_cell = ClimateDataCell.objects.map_cell_for_lat_lon(0.1, 0.1, self.nex_gddp)
        self.assertEqual(target_map_cell.lat, map_cell.lat)
        self.assertEqual(target_map_cell.lon, map_cell.lon)

    def test_map_cell_for_lat_lon_upper_bound(self):
        target_map_cell = ClimateDataCell.objects.create(lat=Decimal(0.25), lon=Decimal(0.25))
        self._make_data_for_map_cell(target_map_cell)
        map_cell = ClimateDataCell.objects.map_cell_for_lat_lon(0.2, 0.23, self.nex_gddp)
        self.assertEqual(target_map_cell.lat, map_cell.lat)
        self.assertEqual(target_map_cell.lon, map_cell.lon)

    def test_map_cell_for_lat_lon_negative(self):
        target_map_cell = ClimateDataCell.objects.create(lat=Decimal(-0.25), lon=Decimal(1.25))
        self._make_data_for_map_cell(target_map_cell)
        map_cell = ClimateDataCell.objects.map_cell_for_lat_lon(-0.2, 1.23, self.nex_gddp)
        self.assertEqual(target_map_cell.lat, map_cell.lat)
        self.assertEqual(target_map_cell.lon, map_cell.lon)

    def test_map_cell_for_lat_lon_fails(self):
        target_map_cell = ClimateDataCell.objects.create(lat=Decimal(-0.25), lon=Decimal(1.25))
        self._make_data_for_map_cell(target_map_cell)
        with self.assertRaises(ClimateDataCell.DoesNotExist):
            ClimateDataCell.objects.map_cell_for_lat_lon(0, 0, self.nex_gddp)

    def test_filter_map_cell_results_by_dataset(self):
        # The lat/lon values defined here and for target_map_cell should be less than
        # half the loca cell size width so that queries for both dataset match geom bounds
        lat = 0.0
        lon = 0.0
        target_map_cell_x = Decimal(lon + float(self.loca.cell_size_x) / 4)
        target_map_cell_y = Decimal(lat + float(self.loca.cell_size_y) / 4)
        target_map_cell = ClimateDataCell.objects.create(lat=target_map_cell_x,
                                                         lon=target_map_cell_y)
        self._make_data_for_map_cell(target_map_cell)
        # First request should succeed and return our map_cell because there is data for that
        #   dataset + map_cell in range
        map_cell = ClimateDataCell.objects.map_cell_for_lat_lon(lat, lon, self.nex_gddp)
        self.assertEqual(target_map_cell.pk, map_cell.pk)
        self.assertEqual(target_map_cell.pk, map_cell.pk)

        # Second request should fail, since there's no data for the dataset + map_cell combo
        with self.assertRaises(ClimateDataCell.DoesNotExist):
            ClimateDataCell.objects.map_cell_for_lat_lon(lat, lon, self.loca)
