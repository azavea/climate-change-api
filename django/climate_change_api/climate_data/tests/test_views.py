from django.core.urlresolvers import reverse

from rest_framework import status
from rest_framework.test import APITestCase

from climate_data.tests.factories import generate_climate_data


class ClimateDataViewTestCase(APITestCase):

    def test_basic_filtering(self):

        generate_climate_data()

        url = reverse('climatedata-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 295)
