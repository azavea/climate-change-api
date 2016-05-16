from __future__ import unicode_literals

from django.contrib.gis.db import models


class ClimateModel(models.Model):
    """Model representing a climate model"""

    name = models.CharField(max_length=40)


class City(models.Model):
    """Model representing a city"""

    geom = models.PointField()

    name = models.CharField(max_length=40)
    admin = models.CharField(max_length=40)


class ClimateData(models.Model):

    city = models.ForeignKey(City)
    climate_model = models.ForeignKey(ClimateModel)

    year = models.PositiveSmallIntegerField()
    day_of_year = models.PositiveSmallIntegerField()

    tasmin = models.FloatField(null=True,
                               help_text='Daily Minimum Near-Surface Air Temperature, Degrees Kelvin')  # NOQA
    tasmax = models.FloatField(null=True,
                               help_text='Daily Maximum Near-Surface Air Temperature, Degrees Kelvin')  # NOQA
    pr = models.FloatField(null=True,
                           help_text='Precipitation (mean of the daily precipitation rate), kg m-2 s-1')  # NOQA

    class Meta:
        unique_together = ('city', 'climate_model', 'year', 'day_of_year')
