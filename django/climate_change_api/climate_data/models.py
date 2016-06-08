from __future__ import unicode_literals

from django.contrib.gis.db import models


class ClimateModel(models.Model):
    """
    Model representing a climate model

    We are storing a table of climate models as an alternative to storing the
    climate model name in CharFields on the ClimateData django model in order
    to make sure that table, which will store a large amount of rows, stays
    as small as possible.
    """

    name = models.CharField(max_length=40, unique=True)

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


class ClimateData(models.Model):

    city = models.ForeignKey(City)
    climate_model = models.ForeignKey(ClimateModel)
    scenario = models.ForeignKey(Scenario)

    year = models.PositiveSmallIntegerField()
    day_of_year = models.PositiveSmallIntegerField()

    tasmin = models.FloatField(null=True,
                               help_text='Daily Minimum Near-Surface Air Temperature, Kelvin')
    tasmax = models.FloatField(null=True,
                               help_text='Daily Maximum Near-Surface Air Temperature, Kelvin')
    pr = models.FloatField(null=True,
                           help_text='Precipitation (mean of the daily precipitation rate), kg m-2 s-1')  # NOQA

    class Meta:
        unique_together = ('city', 'scenario', 'climate_model', 'year', 'day_of_year')
