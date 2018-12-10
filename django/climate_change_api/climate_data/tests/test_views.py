from django.contrib.gis.geos import MultiPolygon, Polygon
from django.urls import reverse
from django.utils.http import urlencode

from rest_framework import status

from climate_data.models import CityBoundary, ClimateDataYear
from climate_data.tests.mixins import ClimateDataSetupMixin, CityDataSetupMixin
from climate_data.tests.factories import ClimateDatasetFactory, ScenarioFactory

from user_management.tests.api_test_case import CCAPITestCase


class ClimateDataViewTestCase(ClimateDataSetupMixin, CCAPITestCase):

    def test_complete_response(self):

        dataset = ClimateDatasetFactory(name='NEX-GDDP')
        url = reverse('climatedata-list',
                      kwargs={'scenario': self.rcp45.name, 'city': self.city1.id})

        response = self.client.get(url, {'dataset': dataset.name})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['city']['id'], self.city1.id)
        self.assertEqual(response.data['scenario'], self.rcp45.name)
        self.assertEqual(response.data['variables'], ClimateDataYear.VARIABLE_CHOICES)
        self.assertEqual(response.data['climate_models'], [m.name for m in
                         dataset.models.all()])
        self.assertEqual(len(response.data['data']), 4)

    def test_scenario_filter(self):
        dataset = ClimateDatasetFactory(name='NEX-GDDP')
        url = reverse('climatedata-list',
                      kwargs={'scenario': self.rcp85.name, 'city': self.city1.id})

        response = self.client.get(url, {'dataset': dataset.name})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['city']['id'], self.city1.id)
        self.assertEqual(response.data['scenario'], self.rcp85.name)
        self.assertEqual(response.data['variables'], ClimateDataYear.VARIABLE_CHOICES)
        self.assertEqual(response.data['climate_models'], [m.name for m in
                         dataset.models.all()])
        self.assertEqual(len(response.data['data']), 1)

    def test_city_filter(self):
        dataset = ClimateDatasetFactory(name='NEX-GDDP')
        url = reverse('climatedata-list',
                      kwargs={'scenario': self.rcp45.name, 'city': self.city2.id})

        response = self.client.get(url, {'dataset': dataset.name})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['city']['id'], self.city2.id)
        self.assertEqual(response.data['scenario'], self.rcp45.name)
        self.assertEqual(response.data['variables'], ClimateDataYear.VARIABLE_CHOICES)
        self.assertEqual(response.data['climate_models'], [m.name for m in
                         dataset.models.all()])
        self.assertEqual(len(response.data['data']), 0)

    def test_404_if_city_invalid(self):
        url = reverse('climatedata-list',
                      kwargs={'scenario': self.rcp45.name, 'city': 999999})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_404_if_scenario_invalid(self):
        url = reverse('climatedata-list',
                      kwargs={'scenario': 'BADSCENARIO', 'city': self.city1.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_400_if_dataset_invalid(self):
        url = u'%s?%s' % (
            reverse('climatedata-list',
                    kwargs={'scenario': self.rcp45.name,
                            'city': self.city1.id}),
            urlencode({
                'dataset': 'BADDATASET'
            })
        )

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class IndicatorDetailViewTestCase(CCAPITestCase):

    def test_200_if_indicator_valid(self):
        url = reverse('climateindicator-detail',
                      kwargs={'indicator': 'frost_days'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_404_if_indicator_invalid(self):
        url = reverse('climateindicator-detail',
                      kwargs={'indicator': 'notanindicator'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class IndicatorDataViewTestCase(ClimateDataSetupMixin, CCAPITestCase):

    def test_404_if_city_invalid(self):
        url = reverse('climateindicator-get',
                      kwargs={'scenario': self.rcp45.name,
                              'city': 999999,
                              'indicator': 'frost_days'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_404_if_scenario_invalid(self):
        url = reverse('climateindicator-get',
                      kwargs={'scenario': 'BADSCENARIO',
                              'city': self.city1.id,
                              'indicator': 'frost_days'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_404_if_indicator_invalid(self):
        url = reverse('climateindicator-get',
                      kwargs={'scenario': self.rcp45.name,
                              'city': self.city1.id,
                              'indicator': 'notanindicator'})

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_400_if_dataset_invalid(self):
        url = u'%s?%s' % (
            reverse('climateindicator-get',
                    kwargs={'scenario': self.rcp45.name,
                            'city': self.city1.id,
                            'indicator': 'frost_days'}),
            urlencode({
                'dataset': 'BADDATASET'
            })
        )

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class ClimateModelViewSetTestCase(CCAPITestCase):

    def test_filtering(self):
        """Should allow equality filtering on name."""
        # ClimateModel data now loaded by migration

        url = reverse('climatemodel-list')

        # Ensure no filters pull all data
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 33)

        # Begin tests for filtering
        response = self.client.get(url, {'name': 'CCSM4'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)


class ScenarioViewSetTestCase(CCAPITestCase):

    def test_filtering(self):
        """Should allow equality filtering on name."""
        ScenarioFactory(name='RCP45')
        ScenarioFactory(name='RCP85')

        url = reverse('scenario-list')

        # Ensure no filters pull all data
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

        # Begin tests for filtering
        response = self.client.get(url, {'name': 'RCP45'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)


class CityViewSetTestCase(CityDataSetupMixin, CCAPITestCase):

    def check_city_list(self, geojson, city_ids):
        """Compare geojson response against a particular response order with a helper."""
        for feature, city_id in zip(geojson['features'], city_ids):
            self.assertEqual(feature['id'], city_id)

    def test_filtering_name(self):
        """Should allow icontains filtering on name."""
        url = reverse('city-list')

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 3)

        response = self.client.get(url, {'name': 'phila'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

    def test_filtering_admin(self):
        """Should allow icontains filtering on admin."""
        url = reverse('city-list')

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 3)

        response = self.client.get(url, {'admin': 'us'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)

    def test_filtering_population(self):
        """Should allow range filtering on population."""
        url = reverse('city-list')

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 3)

        # Tests inclusive bounds
        response = self.client.get(url, {'population_gte': 20})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)

        # Tests inclusive bounds
        response = self.client.get(url, {'population_lte': 10})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

        # Test population exact doesn't work
        response = self.client.get(url, {'population': 7})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 3)

    def test_filtering_region(self):
        """Should allow filtering on region."""
        url = reverse('city-list')

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 3)

        response = self.client.get(url, {'region': self.region.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)

    def test_filtering_search(self):
        """Should allow search filtering."""
        url = reverse('city-list')

        response = self.client.get(url, {'search': 'us'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)

        response = self.client.get(url, {'search': 'lond'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

    def test_list_ordering(self):
        """Ensure this endpoint can be sorted."""
        url = reverse('city-list')

        response = self.client.get(url, {'ordering': '-population'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.check_city_list(response.data, [self.city3.id, self.city2.id, self.city1.id])

        response = self.client.get(url, {'ordering': 'admin,name'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.check_city_list(response.data, [self.city3.id, self.city1.id, self.city2.id])

        response = self.client.get(url, {'ordering': 'region,-name'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.check_city_list(response.data, [self.city2.id, self.city1.id, self.city3.id])

    def test_list_is_geojson(self):
        """Ensure this endpoint is geojson-like."""
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
        """Ensure this endpoint is geojson-like."""
        url = reverse('city-detail', args=[self.city1.id])

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        geojson = response.data
        fields = ('id', 'type', 'geometry', 'properties',)
        for field in fields:
            self.assertIn(field, geojson)

    def test_detail_doesnt_have_boundary(self):
        """Ensure this endpoint is geojson-like."""
        url = reverse('city-detail', args=[self.city1.id])

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        geojson = response.data
        self.assertNotIn('boundary', geojson['properties'])

    def test_detail_has_proximity_object(self):
        """Ensure this endpoint is geojson-like."""
        url = reverse('city-detail', args=[self.city1.id])

        response = self.client.get(url)
        self.assertIn('ocean', response.data['properties']['proximity'])

    def test_bbox_filtering(self):
        """Ensure this endpoint has bbox filtering via in_bbox=minlon,minlat,maxlon,maxlat."""
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

    def test_boundary_404_if_no_data(self):
        url = reverse('city-boundary', args=[self.city1.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_boundary(self):

        geom = MultiPolygon(Polygon([[0, 0], [1, 1], [2, 2], [0, 0]]))
        CityBoundary.objects.create(city=self.city1,
                                    geom=geom,
                                    boundary_type='TEST',
                                    source='TEST')

        url = reverse('city-boundary', args=[self.city1.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        geojson = response.data
        fields = ('type', 'geometry', 'properties',)
        for field in fields:
            self.assertIn(field, geojson)

    def test_nearest_endpoint(self):
        """Test getting the list of nearest cities from a separate endpoint."""
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
        """Test that nearest throws proper errors when given bad data."""
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


class LatLonMapCellListViewTestCase(ClimateDataSetupMixin, CCAPITestCase):

    def test_querying_returns_data(self):
        """Should retrieve data for point."""
        url = reverse('lat-lon-map-cell-list', kwargs={
            'lat': self.mapcell.geom.y, 'lon': self.mapcell.geom.x
        })
        response = self.client.get(url)
        self.assertEqual(1, len(response.data))

    def test_querying_returns_200_status(self):
        """Should return 200 status code for point."""
        url = reverse('lat-lon-map-cell-list', kwargs={
            'lat': self.mapcell.geom.y, 'lon': self.mapcell.geom.x
        })
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_returned_data_contains_datasets(self):
        """Data should contains list of datasets."""
        url = reverse('lat-lon-map-cell-list', kwargs={
            'lat': self.mapcell.geom.y, 'lon': self.mapcell.geom.x
        })
        response = self.client.get(url)
        self.assertIn('dataset', response.data[0]['properties'])

    def test_returned_data_contains_is_coastal(self):
        """Data should contain proximity to coast field."""
        url = reverse('lat-lon-map-cell-list', kwargs={
            'lat': self.mapcell.geom.y, 'lon': self.mapcell.geom.x
        })
        response = self.client.get(url)
        self.assertIn('proximity', response.data[0]['properties'])

    def test_no_data_returns_404_status(self):
        """Should return 404 for point without data."""
        url = reverse('lat-lon-map-cell-list', kwargs={'lat': 17, 'lon': 17})
        response = self.client.get(url)
        self.assertEqual(404, response.status_code)


class LatLonMapCellDistanceListViewTestCase(ClimateDataSetupMixin, CCAPITestCase):

    def test_querying_returns_data(self):
        """Should retrieve data for point."""
        url = reverse('lat-lon-map-cell-distance-list', kwargs={
            'lat': self.mapcell.geom.y, 'lon': self.mapcell.geom.x, 'distance': 5000
        })
        response = self.client.get(url)
        self.assertEqual(1, len(response.data))

    def test_querying_returns_200_status(self):
        """Should return 200 status code for point."""
        url = reverse('lat-lon-map-cell-distance-list', kwargs={
            'lat': self.mapcell.geom.y, 'lon': self.mapcell.geom.x, 'distance': 5000
        })
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_returned_data_contains_distances(self):
        """Data should contain distances."""
        url = reverse('lat-lon-map-cell-distance-list', kwargs={
            'lat': self.mapcell.geom.y, 'lon': self.mapcell.geom.x, 'distance': 5000
        })
        response = self.client.get(url)
        self.assertIn('distance_meters', response.data[0]['properties'])

    def test_no_data_returns_empty_list(self):
        """Should return empty for point without data in the distance radius."""
        url = reverse('lat-lon-map-cell-distance-list', kwargs={'lat': 17,
                      'lon': 17, 'distance': 0})
        response = self.client.get(url)
        self.assertEqual(0, len(response.data))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
