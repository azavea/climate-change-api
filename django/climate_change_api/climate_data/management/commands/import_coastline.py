import logging

from esridump.dumper import EsriDumper

from django.core.management.base import BaseCommand

# from django.contrib.gis.db.models import Union
from django.contrib.gis.geos import LineString

from climate_data.models import Coastline

logger = logging.getLogger(__name__)


# ArcGIS server hosting NOAA coastline data
COAST_URL = 'https://encdirect.noaa.gov/arcgis/rest/services/encdirect/enc_coastal/MapServer/70'
COASTAL_SRID = 4326


class Command(BaseCommand):
    """Imports coast outline from NOAA."""

    def handle(self, *args, **options):
        logger.info('Running NOAA coastline import')

        dumper = EsriDumper(COAST_URL)

        for feature in dumper:
            object_id = feature['properties']['OBJECTID']
            line_string = LineString(feature['geometry']['coordinates'],
                                     srid=COASTAL_SRID)

            Coastline.objects.update_or_create(objectid=object_id, defaults={'geom': line_string})
            logger.info('Loaded coastline LineString: %s', object_id)

        logger.info('Got shoreline features downloaded')

        # TODO: bounds check with cities

        # multi_line = Coastline.objects.aggregate(Collect('geom'))['geom__collect']
        # buff = multi_line.buffer(0.0001).unary_union
        # coastal_cities = CityBoundary.objects.filter(geom__intersects=buff)
        # get invalid geoms
        # bad = Coastline.objects.filter(geom__isvalid=False)
        # Too few points in geometry component
        # with .simplify(0.001)
