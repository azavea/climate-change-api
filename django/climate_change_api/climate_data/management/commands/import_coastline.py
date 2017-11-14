import logging

import json
from esridump.dumper import EsriDumper

from django.core.management.base import BaseCommand

from django.contrib.gis.geos import GEOSGeometry, LineString

from climate_data.models import Coastline

logger = logging.getLogger(__name__)


# ArcGIS server hosting NOAA coastline data
COAST_URL = 'https://encdirect.noaa.gov/arcgis/rest/services/encdirect/enc_coastal/MapServer/70'
COASTAL_SRID = 4326


class Command(BaseCommand):
    """Imports coast outline from NOAA.
    """

    def handle(self, *args, **options):
        logger.info('Running command handler. TODO: import coastline')

        dumper = EsriDumper(COAST_URL)

        for feature in dumper:
            object_id = feature['properties']['OBJECTID']
            line_string = LineString(feature['geometry']['coordinates'],
                                     srid=COASTAL_SRID).simplify(0.001)

            Coastline.objects.update_or_create(geom=line_string, objectid=object_id)
            logger.info('Loaded coastline LineString: %s', object_id)

        logger.info('Got shoreline features downloaded')
