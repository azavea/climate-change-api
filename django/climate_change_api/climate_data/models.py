from __future__ import unicode_literals

from django.db.models import SET_NULL
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
    label = models.CharField(max_length=128, blank=True, null=True)
    base_time = models.DateField(null=True)

    def __str__(self):
        return self.name


class Scenario(models.Model):
    """ Model representing a particular climate emissions scenario

    TODO: Could add more fields here, such as links to sources and citations

    """
    name = models.CharField(max_length=48, unique=True)
    label = models.CharField(max_length=128, blank=True, null=True)
    description = models.CharField(max_length=4096, blank=True, null=True)

    def __str__(self):
        return self.name


class CityManager(models.Manager):
    def nearest(self, point, limit=1):
        """ Get the nearest N cities to the given point.

        Uses an index distance search on geography.

        Returns a list rather than a queryset because the raw query returns a RawQuerySet which
        the view can't paginate because it doesn't support having 'len()' called on it. Loading
        the whole list of cities in before paginating it is potentially inefficient, but for
        smallish values of 'limit', which is the normal case, there's little to no actual cost.

        :arg Point point: A Point object to find the nearest cities to
        :arg int limit: Number of cities to return (default: 1)
        :returns: list[City]
        """
        query = """
            SELECT id, name, geom,
                   ST_Distance(_geog, ST_GeogFromText(%(point)s)) AS distance
            FROM {table}
            ORDER BY _geog <-> ST_GeogFromText(%(point)s) ASC
            LIMIT %(limit)s;
            """.format(table=self.model._meta.db_table)
        params = {
            'point': point.wkt,
            'limit': limit
        }
        return list(self.raw(query, params))


class ClimateDataSource(models.Model):
    model = models.ForeignKey(ClimateModel)
    scenario = models.ForeignKey(Scenario)
    year = models.PositiveSmallIntegerField()

    class Meta:
        unique_together = ('model', 'scenario', 'year')


class ClimateDataCell(models.Model):
    lat = models.DecimalField(max_digits=6, decimal_places=3)
    lon = models.DecimalField(max_digits=6, decimal_places=3)

    class Meta:
        unique_together = ('lat', 'lon')


class City(models.Model):
    """Model representing a city

    Keeps a copy of the geometry in a geography field to enable accurate indexed distance ordering.
    """

    geom = models.PointField()
    _geog = models.PointField(geography=True)

    map_cell = TinyForeignKey(ClimateDataCell, on_delete=SET_NULL, null=True)

    name = models.CharField(max_length=40)
    admin = models.CharField(max_length=40)

    objects = CityManager()

    def __str__(self):
        return '{}, {}'.format(self.name, self.admin)

    class Meta:
        unique_together = ('name', 'admin')

    def save(self, *args, **kwargs):
        """ Override save to keep the geography field up to date """
        self._geog = self.geom
        super(City, self).save(*args, **kwargs)


class ClimateData(models.Model):

    VARIABLE_CHOICES = set(('tasmax', 'tasmin', 'pr',))

    map_cell = TinyForeignKey(ClimateDataCell)
    data_source = TinyForeignKey(ClimateDataSource)
    day_of_year = models.PositiveSmallIntegerField()

    tasmin = models.FloatField(null=True,
                               help_text='Daily Minimum Near-Surface Air Temperature, Kelvin')
    tasmax = models.FloatField(null=True,
                               help_text='Daily Maximum Near-Surface Air Temperature, Kelvin')
    pr = models.FloatField(null=True,
                           help_text='Precipitation (mean of the daily precipitation rate), kg m-2 s-1')  # NOQA

    class Meta:
        unique_together = ('map_cell', 'data_source', 'day_of_year')
        index_together = ('map_cell', 'data_source')


class HistoricAverageClimateData(models.Model):
    """ Model storing computed averages for historic climate data from 1961-1990.

    Used in computing the heat wave duration index (HWDI) and extreme precipitation (R95T).
    http://www.vsamp.com/resume/publications/Frich_et_al.pdf

    Derived from raw historic ClimateData, and stored separately partly for performance, and
    partly for development environment convenience (averages can be loaded from a fixture,
    whereas the raw data is too large to load practically in development.)
    """

    city = TinyForeignKey(City)

    # date string in format 'MM-DD'
    month_day = models.CharField(null=False, blank=False, max_length=5)

    tasmin = models.FloatField(null=True,
                               help_text='Historic Average Daily Minimum Near-Surface Air Temperature 1961-1990, Kelvin')  # NOQA
    tasmax = models.FloatField(null=True,
                               help_text='Historic Average Daily Maximum Near-Surface Air Temperature 1961-1990, Kelvin')  # NOQA
    pr = models.FloatField(null=True,
                           help_text='Historic Average Precipitation (mean of the daily precipitation rate) 1961-1990, kg m-2 s-1')  # NOQA

    class Meta:
        unique_together = ('city', 'month_day')
        index_together = ('city', 'month_day')
