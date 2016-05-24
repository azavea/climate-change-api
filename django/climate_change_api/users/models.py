from __future__ import unicode_literals

from django.db import models
from django.contrib.auth.models import AbstractUser


class APIUser(AbstractUser):

    organization = models.CharField(blank=True, null=True, max_length=255)
