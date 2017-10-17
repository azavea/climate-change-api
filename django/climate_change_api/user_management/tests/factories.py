from factory.django import DjangoModelFactory
from factory import PostGenerationMethodCall

from user_management.models import UserProfile, ClimateUser


class UserFactory(DjangoModelFactory):

    first_name = 'Hei'
    last_name = 'Bai'
    email = 'panda@wwf.org'
    password = PostGenerationMethodCall('set_password', 'iucnendangered')

    class Meta:
        model = ClimateUser
        django_get_or_create = ('email', )


class UserProfileFactory(DjangoModelFactory):

    user = None
    organization = 'WWF'

    class Meta:
        model = UserProfile
        django_get_or_create = ('user', )

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """Override to lazily instantiate user from factory.

        Otherwise, `UserFactory` gets invoked before the test suite has switched over
        to the test database.
        """
        kwargs['user'] = UserFactory()
        return super(UserProfileFactory, cls)._create(model_class, *args, **kwargs)
