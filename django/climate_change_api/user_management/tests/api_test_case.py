from django.test import Client, TestCase
from django.contrib.auth.models import Group, User

from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.core.urlresolvers import reverse

from rest_framework.authtoken.views import obtain_auth_token
from rest_framework.authtoken.models import Token
from rest_framework import status
from rest_framework.test import APIClient, APITestCase, force_authenticate

from user_management.tests.factories import UserFactory, UserProfileFactory
from user_management.models import UserProfile


class CCAPITestCase(APITestCase):

    def setUp(self):
        super(CCAPITestCase, self).setUp()

        # Create user with profile and auth token
        self.profile = UserProfileFactory()
        self.user = self.profile.user
        self.create_user_token()

        # Log into API
        self.client = APIClient()
        self.client.force_authenticate(user=self.user, token=self.user.auth_token)

    def create_user_token(self):

        self.token = Token.objects.create(user=self.user)
        self.token.save()
        return self.token


class UserTestCase(TestCase):

    def test_login(self):

        self.client = Client()
        url = '/accounts/login/'
        response = self.client.post(url, {'username': 'Panda', 'password': 'iucnendangered'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
