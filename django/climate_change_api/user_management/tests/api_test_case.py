"""Helpers for creating API test cases."""

from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from climate_change_api.tests import DummyCacheTestCase
from user_management.tests.factories import UserProfileFactory


class CCAPITestCase(DummyCacheTestCase):
    """Base TestCase class used for all CC API tests."""

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

        self.token, created = Token.objects.get_or_create(user=self.user)
        if created:
            self.token.save()
        return self.token
