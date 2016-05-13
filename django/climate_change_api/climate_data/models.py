from __future__ import unicode_literals

from django.contrib.gis.db import models


class ClimateModel(models.Model):
    """Model representing a climate model"""

    name = models.CharField(max_length=40)

    objects = models.GeoManager()


class City(models.Model):
    """Model representing a city"""

    geom = models.PointField()

    name = models.CharField(max_length=40)
    admin = models.CharField(max_length=40)

    population = models.PositiveIntegerField()

    objects = models.GeoManager()


class ClimateData(models.Model):

    city = models.ForeignKey(City)
    climate_model = models.ForeignKey(ClimateModel)

    year = models.PositiveSmallIntegerField()
    day_of_year = models.PositiveSmallIntegerField()

    tasmin = models.FloatField(null=True)
    tasmax = models.FloatField(null=True)
    pr = models.FloatField(null=True)

    objects = models.GeoManager()

    class Meta:
        unique_together = ('city', 'climate_model', 'year', 'day_of_year')
