from rest_framework import status
from rest_framework.test import APIClient

from users.models import APIUser
from rest_framework.test import APITestCase


class UsersTestCase(APITestCase):

    def create_user(self):
        user1 = APIUser.objects.create_user(id=1, username='WWF', first_name='Panda', last_name='Bear',
            email='pandabear@wwf.org', password='p@nd@5', is_staff=False, is_superuser=False,
            organization='World Wildlife Fund')
        return user1

    def test_user_created(self):
        panda = self.create_user()
        self.assertEqual(panda.first_name, 'Panda')
