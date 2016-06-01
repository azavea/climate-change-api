from __future__ import unicode_literals

from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):
    def __unicode__(self):
        return '{}'.format(self.user.username)

    user = models.OneToOneField(User)
    organization = models.CharField(max_length=255, blank=True, default='')

    def save(self, *args, **kwargs):
        return super(UserProfile, self).save(*args, **kwargs)
