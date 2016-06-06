from __future__ import unicode_literals

from django.db import models
from django.contrib.auth.models import User

from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework.authtoken.models import Token


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    """ Create auth token upon new user creation.
    Account access still requires email verification """
    if created:
        Token.objects.create(user=instance)


class UserProfile(models.Model):
    """ Holds additional personal fields to associate with a user """

    def __unicode__(self):
        return '{}'.format(self.user.username)

    user = models.OneToOneField(User)
    organization = models.CharField(max_length=255, blank=True, default='')

    @classmethod
    def create(self, user):
        profile = self(user=user)
        return profile

    def save(self, *args, **kwargs):
        return super(UserProfile, self).save(*args, **kwargs)
