import logging

from django.contrib.gis.db import models
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import Point, Polygon
from django.contrib.postgres.fields.array import ArrayField
from django.contrib.postgres.aggregates import ArrayAgg
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db.models import CASCADE, SET_NULL

from climate_data.geo_boundary import census

logger = logging.getLogger(__name__)


class TinyForeignKey(models.ForeignKey):
    def db_type(self, connection):
        return models.SmallIntegerField().db_type(connection=connection)


class TinyOneToOne(models.OneToOneField):
    def db_type(self, connection):
        return models.SmallIntegerField().db_type(connection=connection)


# TODO: Remove after upgrading to Django 2.0
class DistinctArrayAgg(ArrayAgg):
    template = '%(function)s(DISTINCT %(expressions)s)'

    @property
    def output_field(self):
        return ArrayField(self.source_expressions[0].output_field)


def get_datasets():
    return [ClimateDataset.Datasets.LOCA, ClimateDataset.Datasets.NEX_GDDP]


class ClimateDataset(models.Model):
    """Model representing a particular climate projection dataset."""

    class Datasets:
        LOCA = 'LOCA'
        NEX_GDDP = 'NEX-GDDP'

        CHOICES = (
            (LOCA, LOCA),
            (NEX_GDDP, NEX_GDDP),
        )

    name = models.CharField(max_length=48, unique=True, choices=Datasets.CHOICES)
    label = models.CharField(max_length=128, blank=True, null=True)
    description = models.CharField(max_length=4096, blank=True, null=True)
    url = models.URLField(blank=True, null=True)
    cell_size_x = models.DecimalField(max_digits=8, decimal_places=4, blank=True, null=True)
    cell_size_y = models.DecimalField(max_digits=8, decimal_places=4, blank=True, null=True)

    models = models.ManyToManyField('ClimateModel', related_name='datasets')

    _DATASETS = None

    def has_model(self, climate_model_name):
        """Return true if dataset contains the specified model, false otherwise."""
        return self.models.filter(name=climate_model_name).exists()

    @classmethod
    def datasets(cls):
        """Return iterable of valid dataset names."""
        if cls._DATASETS is None:
            cls._DATASETS = [c.name for c in ClimateDataset.objects.all()]
        return cls._DATASETS

    def __str__(self):
        """Return pretty string representation of model, used by Django for field labels."""
        return self.name

    def natural_key(self):
        return (self.name,)


class ClimateModel(models.Model):
    """Model representing a climate model.

    We are storing a table of climate models as an alternative to storing the
    climate model name in CharFields on the ClimateDataYear django model in order
    to make sure that table, which will store a large amount of rows, stays
    as small as possible.
    """

    name = models.CharField(max_length=40, unique=True)
    label = models.CharField(max_length=128, blank=True, null=True)
    base_time = models.DateField(null=True)

    def __str__(self):
        """Return pretty string representation of model, used by Django for field labels."""
        return self.name

    def natural_key(self):
        return (self.name,)


class Scenario(models.Model):
    """Model representing a particular climate emissions scenario.

    TODO: Could add more fields here, such as links to sources and citations
    """

    name = models.CharField(max_length=48, unique=True)
    label = models.CharField(max_length=128, blank=True, null=True)
    description = models.CharField(max_length=4096, blank=True, null=True)
    alias = models.CharField(max_length=128, blank=True, null=True)

    def __str__(self):
        """Return pretty string representation of model, used by Django for field labels."""
        return self.name

    def natural_key(self):
        return (self.name,)


class CityManager(models.Manager):
    def nearest(self, point, limit=1):
        """Get the nearest N cities to the given point.

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

    def get_by_natural_key(self, name, admin):
        return self.get(name=name, admin=admin)


class ClimateDataSource(models.Model):
    model = models.ForeignKey(ClimateModel)
    scenario = models.ForeignKey(Scenario)
    year = models.PositiveSmallIntegerField()
    import_completed = models.BooleanField(default=False)
    dataset = models.ForeignKey(ClimateDataset)

    class Meta:
        unique_together = ('model', 'scenario', 'year', 'dataset')

    def natural_key(self):
        return (self.model, self.scenario, self.year, self.dataset)

    def __str__(self):
        """Override str for useful info in console."""
        return '{}, {}, {}'.format(self.scenario, self.model, self.year)

    def save(self, *args, **kwargs):
        if not self.dataset.has_model(self.model.name):
            raise ValueError('Dataset {} does not contain model {}'.format(self.dataset.name,
                                                                           self.model.name))
        super(ClimateDataSource, self).save(*args, **kwargs)


class ClimateDataCellManager(models.Manager):
    def map_cells_for_lat_lon(self, lat, lon, distance=0):
        """Return the ClimateDataCells for a given point, as well as any cells within the given distance.

        Each cell is annotated with its distance from the given search point, as a Distance object
        that offers conversion to various units.

        The queryset is ordered by distance.
        """
        map_cells = self._map_cells_at_lat_lon(lat, lon)
        if distance > 0:
            map_cells = map_cells | self._map_cells_near_lat_lon(lat, lon, distance)

        return map_cells.annotate(
            datasets=DistinctArrayAgg('climatedatayear__data_source__dataset__name'),
        ).order_by('distance')

    def _map_cells_at_lat_lon(self, lat, lon):
        map_cell_ids = []
        # The query to ClimateDataset could be problematic, but there are only 2 so it's not really
        for dataset in ClimateDataset.objects.all():
            map_cell_id = self._map_cell_id_at_lat_lon(lat, lon, dataset)
            if map_cell_id is not None:
                map_cell_ids.append(map_cell_id)

        search_point = Point(lon, lat, srid=4326)
        return ClimateDataCell.objects.filter(id__in=map_cell_ids).annotate(
            distance=Distance('geog', search_point)
        )

    def _map_cell_id_at_lat_lon(self, lat, lon, dataset):
        x_width = float(dataset.cell_size_x) / 2
        y_width = float(dataset.cell_size_y) / 2
        search_box = Polygon((
            (lon - x_width, lat - y_width),
            (lon - x_width, lat + y_width),
            (lon + x_width, lat + y_width),
            (lon + x_width, lat - y_width),
            (lon - x_width, lat - y_width),
        ))
        search_point = Point(lon, lat, srid=4326)
        map_cell_ids = (ClimateDataCell.objects.filter(geom__within=search_box)
                                               .annotate(distance=Distance('geog', search_point))
                                               .values_list('id', flat=True)
                                               .order_by('distance'))
        cells_checked = 0
        for map_cell_id in map_cell_ids:
            cells_checked += 1
            exists_for_dataset = (ClimateDataYear.objects.filter(map_cell_id=map_cell_id,
                                                                 data_source__dataset=dataset)
                                                         .exists())
            if exists_for_dataset:
                if cells_checked > 4:
                    logger.warning('Checked {} cells at point ({}, {}) for dataset {}'
                                   .format(cells_checked, lon, lat, dataset.name))
                return map_cell_id
        if cells_checked > 4:
            logger.warning('Checked {} cells at point ({}, {}) for dataset {}'
                           .format(cells_checked, lon, lat, dataset.name))
        return None

    def _map_cells_near_lat_lon(self, lat, lon, distance):
        search_point = Point(lon, lat, srid=4326)
        return ClimateDataCell.objects.annotate(
            distance=Distance('geog', search_point)
        ).filter(distance__lte=distance)

    def get_by_natural_key(self, lat, lon, dataset):
        return self.get(lat=lat, lon=lon, dataset=dataset)


class ClimateDataCell(models.Model):
    lat = models.DecimalField(max_digits=9, decimal_places=6)
    # Note: This field uses a non-standard range of [0, 360) instead of [-180, 180)
    # This was done to match the source NetCDF data
    lon = models.DecimalField(max_digits=9, decimal_places=6)

    geom = models.PointField(srid=4326, blank=True, null=True)
    geog = models.PointField(geography=True, blank=True, null=True)

    is_coastal = models.BooleanField(default=False)

    objects = ClimateDataCellManager()

    def save(self, *args, **kwargs):
        # Convert saved lon [0, 360) back to [-180, 180)
        lon = self.lon if self.lon < 180 else self.lon - 360
        self.geom = Point(float(lon), float(self.lat), srid=4326)
        self.geog = self.geom
        super().save(*args, **kwargs)

    class Meta:
        unique_together = ('lat', 'lon',)

    def natural_key(self):
        return (self.lat, self.lon)

    def __str__(self):
        """Override str for useful info in console."""
        return '{}, {}'.format(self.lat, self.lon)


class HistoricDateRange(models.Model):
    """Helper table abstracting year ranges for historic data aggregations.

    Applies to ClimateDataBaseline and HistoricalAverageClimateDataYear.
    """

    start_year = models.PositiveSmallIntegerField(help_text='Inclusive start year of the period',
                                                  primary_key=True, unique=True)
    end_year = models.PositiveSmallIntegerField(help_text='Inclusive ending year of the period')


class ClimateDataBaseline(models.Model):
    dataset = TinyForeignKey(ClimateDataset)
    map_cell = TinyForeignKey(ClimateDataCell, null=False, related_name='baseline')
    historic_range = TinyForeignKey(HistoricDateRange, null=True)
    percentile = models.IntegerField(null=False)

    tasmin = models.FloatField(null=True,
                               help_text='Historic greatest daily minimum temperature for this percentile for a 30 yr period')  # NOQA: E501
    tasmax = models.FloatField(null=True,
                               help_text='Historic greatest daily maximum temperature for this percentile for a 30 yr period')  # NOQA: E501
    pr = models.FloatField(null=True,
                           help_text='Historic greatest daily precipitation for this percentile for a 30 yr period')  # NOQA: E501

    def natural_key(self):
        return (self.map_cell, self.percentile)

    class Meta:
        unique_together = ('map_cell', 'percentile', 'historic_range', 'dataset')


class CityBoundaryManager(models.Manager):

    def create_for_city(self, city):
        """Given a city, find and create an appropriate CityBoundary for it."""
        geom, boundary_type = census.boundary_from_point(city.geom)

        # TODO: Fall through to other boundary services here

        # Delete any existing boundary before we create a new one
        try:
            city.boundary.delete()
        except ObjectDoesNotExist:
            pass
        city_boundary = self.create(city=city,
                                    geom=geom,
                                    boundary_type=boundary_type,
                                    source='US Census API')
        return city_boundary


class CityBoundary(models.Model):
    """Store the related boundary and a generic string type for a given city.

    This model was left intentionally generic so we can support boundaries from different global
    sources easily.

    The boundary_type field stores values such as 'incorporated place', 'county' or 'postalcode'
    """

    geom = models.MultiPolygonField()
    source = models.CharField(max_length=64)
    boundary_type = models.CharField(max_length=64)
    city = models.OneToOneField('City', on_delete=CASCADE, related_name='boundary')

    objects = CityBoundaryManager()


class Coastline(models.Model):
    """NOAA coastline, as a collection of line strings."""

    objectid = models.IntegerField(unique=True)
    geom = models.LineStringField()

    def __str__(self):
        """Return pretty string representation of model, used by Django for field labels."""
        return "Object ID: {}".format(self.objectid)

    class Meta:
        unique_together = ('objectid',)


class Region(models.Model):
    """A level 2 ecoregion.

    As described in: https://www.epa.gov/eco-research/ecoregions-north-america
    """

    geom = models.GeometryField()

    level1 = models.IntegerField()
    level2 = models.IntegerField()

    level1_description = models.CharField(max_length=64)
    level2_description = models.CharField(max_length=64)

    def __str__(self):
        """Return pretty string representation of model, used by Django for field labels."""
        return "{}.{} {}, {}".format(self.level1,
                                     self.level2,
                                     self.level1_description,
                                     self.level2_description)

    class Meta:
        unique_together = ('level1', 'level2')


class City(models.Model):
    """Model representing a city.

    Keeps a copy of the geometry in a geography field to enable accurate indexed distance ordering.
    """

    geom = models.PointField()
    _geog = models.PointField(geography=True)

    name = models.CharField(max_length=40)
    admin = models.CharField(max_length=40)

    is_coastal = models.BooleanField(default=False)
    population = models.IntegerField(null=True)

    datasets = ArrayField(
        models.CharField(max_length=48, choices=ClimateDataset.Datasets.CHOICES),
        size=2,
        default=get_datasets
    )

    region = models.ForeignKey(Region, on_delete=SET_NULL, null=True)

    objects = CityManager()

    def __str__(self):
        """Return pretty string representation of model, used by Django for field labels."""
        return '{}, {}'.format(self.name, self.admin)

    class Meta:
        unique_together = ('name', 'admin')
        verbose_name_plural = 'cities'

    def get_map_cell(self, dataset):
        """Get the map cell for a given dataset for a given city.

        This method will raise ClimateDataCell.DoesNotExist if no map cell exists for the dataset,
        and ClimateDataCell.MultipleObjectsReturned if too many -- there should only ever be one.

        """
        return ClimateDataCell.objects.get(city_set__city=self, city_set__dataset=dataset)

    def natural_key(self):
        return (self.name, self.admin)

    def clean(self):
        super().clean()
        if len(self.datasets) != len(set(self.datasets)):
            raise ValidationError({'datasets': 'Cannot contain duplicate datasets'})

    def save(self, *args, **kwargs):
        """Override save to keep the geography field up to date."""
        self._geog = self.geom
        super(City, self).save(*args, **kwargs)


class ClimateDataCityCell(models.Model):
    city = models.ForeignKey(City, null=False, related_name='map_cell_set')
    map_cell = models.ForeignKey(ClimateDataCell, null=False, related_name='city_set')
    dataset = TinyForeignKey(ClimateDataset, null=False)

    class Meta:
        # A city can only have one map cell for each dataset
        unique_together = ('city', 'dataset',)


class ClimateDataYear(models.Model):

    VARIABLE_CHOICES = set(('tasmax', 'tasmin', 'pr',))

    id = models.BigAutoField(primary_key=True)
    map_cell = TinyForeignKey(ClimateDataCell)
    data_source = TinyForeignKey(ClimateDataSource)

    tasmin = ArrayField(models.FloatField(),
                        help_text='Daily Minimum Near-Surface Air Temperature, Kelvin')
    tasmax = ArrayField(models.FloatField(),
                        help_text='Daily Maximum Near-Surface Air Temperature, Kelvin')
    pr = ArrayField(models.FloatField(),
                    help_text='Precipitation (mean of the daily precipitation rate), kg m-2 s-1')

    class Meta:
        unique_together = ('map_cell', 'data_source')
        index_together = ('map_cell', 'data_source')

    def natural_key(self):
        return (self.map_cell, self.data_source)


class HistoricAverageClimateDataYear(models.Model):
    """Model storing computed averages for historic climate data for various historic ranges.

    Used in computing the heat wave duration index (HWDI) and heat wave incidents indicators
    http://www.vsamp.com/resume/publications/Frich_et_al.pdf

    Derived from raw historic ClimateData and stored separately for performance and ease of access.
    """

    dataset = TinyForeignKey(ClimateDataset)
    map_cell = TinyForeignKey(ClimateDataCell, related_name='historic_average_array')
    historic_range = TinyForeignKey(HistoricDateRange, null=True)

    tasmin = ArrayField(models.FloatField(),
                        help_text='Historic Average Daily Minimum Near-Surface Air Temperature in Kelvin')  # NOQA: E501
    tasmax = ArrayField(models.FloatField(),
                        help_text='Historic Average Daily Maximum Near-Surface Air Temperature in Kelvin')  # NOQA: E501
    pr = ArrayField(models.FloatField(),
                    help_text='Historic Average Precipitation (mean of the daily precipitation rate) in kg/s/m^2')  # NOQA: E501

    class Meta:
        unique_together = ('map_cell', 'historic_range', 'dataset')
        index_together = ('map_cell', 'historic_range', 'dataset')
