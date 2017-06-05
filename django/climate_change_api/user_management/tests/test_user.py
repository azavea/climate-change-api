from django.test import Client

from climate_change_api.tests import DummyCacheTestCase
from user_management.models import ClimateUser
from user_management.tests.factories import UserProfileFactory

from rest_framework import status


class UserTestCase(DummyCacheTestCase):

    def setUp(self):
        self.profile = UserProfileFactory()
        self.user = self.profile.user

    def test_login(self):

        self.client = Client()
        url = '/accounts/login/'
        response = self.client.post(url, {'username': 'panda@wwf.org',
                                          'password': 'iucnendangered'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_encode_email(self):
        encoded_email = self.user.encode_email()
        self.assertEqual(ClimateUser.objects.from_encoded_email(encoded_email), self.user)
