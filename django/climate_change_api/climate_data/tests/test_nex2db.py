from unittest import mock

from django.test import TestCase

from climate_data.nex2db import Nex2DB
from climate_data.models import ClimateDataCityCell
from climate_data.tests.factories import (
    CityFactory,
    ClimateDataCellFactory,
    ClimateDataCityCellFactory,
    ClimateDataSourceFactory
)


class Nex2dbTestCase(TestCase):
    def test_update_city_map_cell_for_city_without_cell(self):
        datasource = ClimateDataSourceFactory()
        city = CityFactory()
        cell_model = ClimateDataCellFactory(lat=15, lon=15)
        nex2db_mock = mock.Mock()
        nex2db_mock.datasource = datasource

        city_coords = {
            city.id: (15, 15)
        }
        cell_models = {
            (15, 15): cell_model
        }

        Nex2DB.update_city_map_cell(nex2db_mock, city, city_coords, cell_models)

        city_map_cell = ClimateDataCityCell.objects.get(city=city, dataset=datasource.dataset)
        self.assertEqual(city_map_cell.map_cell, cell_model)

    def test_update_city_map_cell_for_city_with_matching_cell(self):
        datasource = ClimateDataSourceFactory()
        city_cell = ClimateDataCityCellFactory(dataset=datasource.dataset)
        city = city_cell.city
        cell_model = city_cell.map_cell

        nex2db_mock = mock.Mock()
        nex2db_mock.datasource = datasource

        city_coords = {
            city.id: (15, 15)
        }
        cell_models = {
            (15, 15): cell_model
        }

        Nex2DB.update_city_map_cell(nex2db_mock, city, city_coords, cell_models)

        city_map_cell = ClimateDataCityCell.objects.get(city=city, dataset=datasource.dataset)
        self.assertEqual(city_map_cell.map_cell, cell_model)

    def test_update_city_map_cell_for_city_with_mismatched_cell(self):
        datasource = ClimateDataSourceFactory()
        cell_model = ClimateDataCellFactory(lat=15, lon=15)
        # Create a city with a different cell model than the one we have in cell_models
        city_cell = ClimateDataCityCellFactory(dataset=datasource.dataset)
        city = city_cell.city

        nex2db_mock = mock.Mock()
        nex2db_mock.datasource = datasource

        city_coords = {
            city.id: (15, 15)
        }
        cell_models = {
            (15, 15): cell_model
        }

        Nex2DB.update_city_map_cell(nex2db_mock, city, city_coords, cell_models)

        # The city's map cell should not have been changed
        city_map_cell = ClimateDataCityCell.objects.get(city=city, dataset=datasource.dataset)
        self.assertNotEqual(city_map_cell.map_cell, cell_model)
