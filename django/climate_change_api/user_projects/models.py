from __future__ import unicode_literals

import uuid

from user_management.models import ClimateUser

from django.contrib.postgres.fields import JSONField
from django.db import models


class Project(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(ClimateUser)

    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    project_data = JSONField()

    def __unicode__(self):
        return unicode(self.id)