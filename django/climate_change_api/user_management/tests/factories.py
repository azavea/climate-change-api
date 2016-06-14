from factory.django import DjangoModelFactory

from user_management.models import UserProfile
from django.contrib.auth.models import User


class UserFactory(DjangoModelFactory):

    username = 'Panda'
    first_name = 'Hei'
    last_name = 'Bai'
    email = 'panda@wwf.org'
    password = 'iucnendangered'

    class Meta:
        model = User
        django_get_or_create = ('username', )


class UserProfileFactory(DjangoModelFactory):

    user = UserFactory()
    organization = 'WWF'

    class Meta:
        model = UserProfile
        django_get_or_create = ('user', )
