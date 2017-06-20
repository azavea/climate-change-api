import base64

from django.core.mail import send_mail

from django.db import models
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser, PermissionsMixin

from django.conf import settings
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework.authtoken.models import Token


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    """Create auth token upon new user creation.

    Account access still requires email verification.
    """
    if created:
        Token.objects.create(user=instance)


def get_default_burst_rate():
    return settings.REST_FRAMEWORK['DEFAULT_THROTTLE_RATES']['burst']


def get_default_sustained_rate():
    return settings.REST_FRAMEWORK['DEFAULT_THROTTLE_RATES']['sustained']


class ClimateUserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        """Create and save a User with the given email and password."""
        if not email:
            raise ValueError('An email must be provided')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(email, password, **extra_fields)

    def from_encoded_email(self, encoded_email):
        """Get a ClimateUser from a base64 bytestring encoded via ClimateUser.encode_email()."""
        email = base64.urlsafe_b64decode(encoded_email).decode('UTF-8')
        return self.get(email=email)


class ClimateUser(AbstractBaseUser, PermissionsMixin):
    objects = ClimateUserManager()

    USERNAME_FIELD = 'email'

    email = models.EmailField(
        verbose_name='email address',
        max_length=255,
        unique=True,
    )

    first_name = models.CharField('first name', max_length=30, blank=True)
    last_name = models.CharField('last name', max_length=30, blank=True)
    is_active = models.BooleanField(
        'active',
        default=True,
        help_text=(
            'Designates whether this user should be treated as active. '
            'Unselect this instead of deleting accounts.'
        ),
    )
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    date_joined = models.DateTimeField('date joined', default=timezone.now)

    burst_rate = models.CharField('burst rate', default=get_default_burst_rate, max_length=20)
    sustained_rate = models.CharField('sustained rate',
                                      default=get_default_sustained_rate,
                                      max_length=20)

    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = 'user'
        verbose_name_plural = 'users'

    def clean(self):
        super(AbstractBaseUser, self).clean()
        self.email = self.__class__.objects.normalize_email(self.email)

    def get_full_name(self):
        """Return the first_name plus the last_name, with a space in between."""
        full_name = '%s %s' % (self.first_name, self.last_name)
        return full_name.strip()

    def get_short_name(self):
        """Return the short name for the user."""
        return self.first_name

    def encode_email(self):
        """Return UTF-8 email string as a urlsafe base64 bytestring."""
        return base64.urlsafe_b64encode(self.email.encode('UTF-8'))

    def email_user(self, subject, message, from_email=None, **kwargs):
        """Send an email to this User."""
        send_mail(subject, message, from_email, [self.email], **kwargs)


class UserProfile(models.Model):
    """Holds additional personal fields to associate with a user."""

    def __str__(self):
        """Return pretty string representation of model."""
        return '{}'.format(self.user.email)

    user = models.OneToOneField(ClimateUser)
    organization = models.CharField(max_length=255, blank=False)

    @classmethod
    def create(self, user):
        profile = self(user=user)
        return profile

    def save(self, *args, **kwargs):
        return super(UserProfile, self).save(*args, **kwargs)
