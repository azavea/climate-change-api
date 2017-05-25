from django.test import Client

from climate_change_api.tests import DummyCacheTestCase

from rest_framework import status


class UserTestCase(DummyCacheTestCase):

    def test_login(self):

        self.client = Client()
        url = '/accounts/login/'
        response = self.client.post(url, {'username': 'panda@wwf.org',
                                          'password': 'iucnendangered'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
