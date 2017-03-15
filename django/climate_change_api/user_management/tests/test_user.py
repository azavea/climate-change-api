from django.test import Client, TestCase

from rest_framework import status


class UserTestCase(TestCase):

    def test_login(self):

        self.client = Client()
        url = '/accounts/login/'
        response = self.client.post(url, {'username': 'panda@wwf.org',
                                          'password': 'iucnendangered'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
