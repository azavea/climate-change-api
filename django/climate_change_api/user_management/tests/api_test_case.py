
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient, APITestCase

from user_management.tests.factories import UserProfileFactory


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
