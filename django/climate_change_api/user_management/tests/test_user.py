from django.test import Client
from django.urls import reverse

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
        url = reverse('auth_login')
        response = self.client.post(url, {'username': 'panda@wwf.org',
                                          'password': 'iucnendangered'},
                                    follow=True)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.context['user'].is_authenticated())
        self.assertRedirects(response, reverse('app_home'))

    def test_encode_email(self):
        encoded_email = self.user.encode_email()
        self.assertEqual(ClimateUser.objects.from_encoded_email(encoded_email), self.user)

    def test_stripped_encoded_email(self):
        encoded_email = self.user.encode_email()
        self.assertTrue(encoded_email.endswith(b'='))
        encoded_email = encoded_email.strip(b'=')
        self.assertEqual(ClimateUser.objects.from_encoded_email(encoded_email), self.user)

    def test_get_token(self):
        url = reverse('get_token')
        response = self.client.post(url, {'email': 'panda@wwf.org',
                                          'password': 'iucnendangered'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.user.auth_token.key, response.data['token'])

    def test_refresh_token(self):
        old_token = self.user.auth_token.key
        url = reverse('refresh_token')
        response = self.client.post(url, {'email': 'panda@wwf.org',
                                          'password': 'iucnendangered'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        new_token = response.data['token']

        self.assertNotEqual(old_token, new_token)
