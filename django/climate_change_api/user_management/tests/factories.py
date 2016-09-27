from factory.django import DjangoModelFactory

from user_management.models import UserProfile, ClimateUser


class UserFactory(DjangoModelFactory):

    first_name = 'Hei'
    last_name = 'Bai'
    email = 'panda@wwf.org'
    password = 'iucnendangered'

    class Meta:
        model = ClimateUser
        django_get_or_create = ('email', )


class UserProfileFactory(DjangoModelFactory):

    user = UserFactory()
    organization = 'WWF'

    class Meta:
        model = UserProfile
        django_get_or_create = ('user', )
