from django.core.urlresolvers import reverse
from django.contrib.gis.geos import Point

from rest_framework import status
from rest_framework.test import APITestCase

from climate_data.tests.factories import (CityFactory,
                                          ClimateModelFactory,
                                          generate_climate_data)


class ClimateDataViewTestCase(APITestCase):

    def test_data_filtering(self):
        """ Ensure get param filtering works as expected for each field

        Do all the checks in one test so we don't have to make multiple expensive calls
        to generate_climate_data()

        Tests min_<field>, max_<field>, <field> for each field

        """
        generate_climate_data()

        url = reverse('climatedata-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 295)

        climate_model = ClimateModelFactory()

        checks = [{
            'field': 'climate_model',
            'value': climate_model.name,
            'count': 148
        }, {
            'field': 'year',
            'value': 2002,
            'count': 98
        }, {
            'field': 'min_year',
            'value': 2002,
            'count': 196
        }, {
            'field': 'max_year',
            'value': 2002,
            'count': 197
        }, {
            'field': 'day_of_year',
            'value': 45,
            'count': 6
        }, {
            'field': 'min_day_of_year',
            'value': 45,
            'count': 30
        }, {
            'field': 'max_day_of_year',
            'value': 10,
            'count': 61
        }, {
            'field': 'tasmin',
            'value': 273,
            'count': 55
        }, {
            'field': 'min_tasmin',
            'value': 275,
            'count': 180
        }, {
            'field': 'max_tasmin',
            'value': 275,
            'count': 175
        }, {
            'field': 'pr',
            'value': 0.0001,
            'count': 1
        }, {
            'field': 'min_pr',
            'value': 0.00015,
            'count': 150
        }, {
            'field': 'max_pr',
            'value': 0.00015,
            'count': 145
        }]

        for check in checks:
            response = self.client.get(url, {check['field']: check['value']})
            msg = 'GET {}={} should have {} results, got {}'.format(check['field'],
                                                                    check['value'],
                                                                    check['count'],
                                                                    response.data['count'])
            self.assertEqual(response.data['count'], check['count'], msg=msg)


class ClimateModelViewSetTestCase(APITestCase):

    def test_filtering(self):
        """ Should allow equality filtering on name """
        ClimateModelFactory(name='ukmet')
        ClimateModelFactory(name='ukmet2')
        ClimateModelFactory(name='ukmet3')

        url = reverse('climatemodel-list')

        # Ensure no filters pull all data
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 3)

        # Begin tests for filtering
        response = self.client.get(url, {'name': 'ukmet'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)


class CityViewSetTestCase(APITestCase):

    def setUp(self):
        self.city1 = CityFactory(name='Philadelphia', admin='us', geom=Point(10, 10))
        self.city2 = CityFactory(name='Washington DC', admin='us', geom=Point(20, 20))
        self.city3 = CityFactory(name='London', admin='uk', geom=Point(30, 30))

    def test_filtering(self):
        """ Should allow equality filtering on text properties """
        url = reverse('city-list')

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 3)

        response = self.client.get(url, {'name': 'Philadelphia'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

        response = self.client.get(url, {'admin': 'us'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)

    def test_list_is_geojson(self):
        """ Ensure this endpoint is geojson-like """
        url = reverse('city-list')

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        geojson = response.data
        self.assertIn('type', geojson)
        self.assertIn('features', geojson)
        self.assertEqual(geojson['type'], 'FeatureCollection')
        self.assertEqual(len(geojson['features']), 3)

        # Also ensure its paginated
        self.assertIn('next', geojson)
        self.assertIn('previous', geojson)

    def test_detail_is_geojson(self):
        """ Ensure this endpoint is geojson-like """
        url = reverse('city-detail', args=[self.city1.id])

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        geojson = response.data
        fields = ('id', 'type', 'geometry', 'properties',)
        for field in fields:
            self.assertIn(field, geojson)

    def test_bbox_filtering(self):
        """ Ensure this endpoint has bbox filtering via in_bbox=minlon,minlat,maxlon,maxlat """
        url = reverse('city-list')

        bbox_string = '0,0,{},{}'.format(self.city1.geom.coords[0] + 1,
                                         self.city1.geom.coords[1] + 1)
        response = self.client.get(url, {'in_bbox': bbox_string})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        feature = response.data['features'][0]
        self.assertEqual(feature['properties']['name'], self.city1.name)

        # should also include features on the edge of the boundary
        # Done via bbox_filter_include_overlapping=True in drf gis InBBoxFilter
        bbox_string = '0,0,{},{}'.format(self.city1.geom.coords[0],
                                         self.city1.geom.coords[1])
        response = self.client.get(url, {'in_bbox': bbox_string})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        feature = response.data['features'][0]
        self.assertEqual(feature['properties']['name'], self.city1.name)

    def test_nearest_endpoint(self):
        """ Test getting the list of nearest cities from a separate endpoint """
        url = reverse('city-nearest')

        # test nearest, ensure it paginates by checking 'count', and defaults limit to 1
        response = self.client.get(url, {'lat': 5, 'lon': 5})
        geojson = response.data
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(geojson['count'], 1)
        feature = geojson['features'][0]
        self.assertEqual(feature['properties']['name'], self.city1.name)

        # Test limit param
        response = self.client.get(url, {'lat': 5, 'lon': 5, 'limit': 2})
        geojson = response.data
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(geojson['count'], 2)
        self.assertEqual(geojson['features'][0]['properties']['name'], self.city1.name)
        self.assertEqual(geojson['features'][1]['properties']['name'], self.city2.name)

    def test_nearest_bad_requests(self):
        """ Test that nearest throws proper errors when given bad data """
        url = reverse('city-nearest')

        response = self.client.get(url, {'lat': 5})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        response = self.client.get(url, {'lon': 5})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        response = self.client.get(url, {'lat': 'foo', 'lon': 5})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        response = self.client.get(url, {'lat': 5, 'lon': 'foo'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        response = self.client.get(url, {'lat': 5, 'lon': 5, 'limit': 'foo'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        response = self.client.get(url, {'lat': 5, 'lon': 5, 'limit': 0})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
