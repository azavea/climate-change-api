from __future__ import unicode_literals

from django.contrib.gis.db import models
from django.utils.translation import ugettext_lazy as _
from django.core import exceptions


class TinyAutoField(models.AutoField):

    def rel_db_type(self, connection):
        return models.SmallIntegerField().db_type(connection=connection)

    def get_internal_type(self):
        return "SmallIntegerField"

    def to_python(self, value):
        if value is None:
            return value
        try:
            return int(value)
        except (TypeError, ValueError):
            raise exceptions.ValidationError(
                _("This value must be a short integer."))


class TinyForeignKey(models.ForeignKey):
    def db_type(self, connection):
        return models.SmallIntegerField().db_type(connection=connection)


class ClimateModel(models.Model):
    """
    Model representing a climate model

    We are storing a table of climate models as an alternative to storing the
    climate model name in CharFields on the ClimateData django model in order
    to make sure that table, which will store a large amount of rows, stays
    as small as possible.
    """

    name = models.CharField(max_length=40, unique=True)
    base_time = models.DateField(null=True)

    def __str__(self):
        return self.name


class Scenario(models.Model):
    """ Model representing a particular climate emissions scenario

    TODO: Could add more fields here, such as links to sources and citations

    """
    name = models.CharField(max_length=48, unique=True)
    description = models.CharField(max_length=4096, blank=True, null=True)

    def __str__(self):
        return self.name


class City(models.Model):
    """Model representing a city"""

    geom = models.PointField()

    name = models.CharField(max_length=40)
    admin = models.CharField(max_length=40)

    def __str__(self):
        return '{}, {}'.format(self.name, self.admin)

    class Meta:
        unique_together = ('name', 'admin')


class ClimateDataSource(models.Model):
    model = models.ForeignKey(ClimateModel)
    scenario = models.ForeignKey(Scenario)
    year = models.PositiveSmallIntegerField()

    class Meta:
        unique_together = ('model', 'scenario', 'year')


class ClimateData(models.Model):

    VARIABLE_CHOICES = set(('tasmax', 'tasmin', 'pr',))

    city = TinyForeignKey(City)
    data_source = TinyForeignKey(ClimateDataSource)
    day_of_year = models.PositiveSmallIntegerField()

    tasmin = models.FloatField(null=True,
                               help_text='Daily Minimum Near-Surface Air Temperature, Kelvin')
    tasmax = models.FloatField(null=True,
                               help_text='Daily Maximum Near-Surface Air Temperature, Kelvin')
    pr = models.FloatField(null=True,
                           help_text='Precipitation (mean of the daily precipitation rate), kg m-2 s-1')  # NOQA

    class Meta:
        unique_together = ('city', 'data_source', 'day_of_year')
