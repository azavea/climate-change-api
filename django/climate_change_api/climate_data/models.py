from __future__ import unicode_literals

from django.contrib.gis.db import models


class ClimateModel(models.Model):
    """Model representing a climate model"""

    id = models.PositiveSmallIntegerField(primary_key=True)
    name = models.CharField(max_length=40)

    objects = models.GeoManager()


class City(models.Model):
    """Model representing a city"""

    id = models.PositiveIntegerField(primary_key=True)
    geom = models.PointField()

    name = models.CharField(max_length=40)
    admin_name = models.CharField(max_length=40)

    climate = models.CharField(max_length=40, null=True)
    precip = models.CharField(max_length=40, null=True)
    temp = models.CharField(max_length=40, null=True)

    continent = models.CharField(max_length=20, null=True)
    gdp_md_est = models.PositiveIntegerField(null=True)

    objects = models.GeoManager()


class PopulationCount(models.Model):
    id = models.PositiveIntegerField(primary_key=True)

    city = models.ForeignKey(City)
    year = models.PositiveSmallIntegerField()
    pop = models.PositiveIntegerField()

    class Meta:
        unique_together = ('city', 'year')


class ClimateData(models.Model):
    id = models.PositiveIntegerField(primary_key=True)

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
