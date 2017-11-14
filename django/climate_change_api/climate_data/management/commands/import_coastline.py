import logging

import json
from esridump.dumper import EsriDumper

from django.core.management.base import BaseCommand

#from climate_data.models import City, Region
#from django.contrib.gis.geos import GEOSGeometry, MultiPolygon

logger = logging.getLogger(__name__)


# ArcGIS server hosting NOAA coastline data
COAST_URL = 'https://encdirect.noaa.gov/arcgis/rest/services/encdirect/enc_coastal/MapServer/70'


class Command(BaseCommand):
    """Imports coast outline from NOAA.
    """

    def handle(self, *args, **options):
        logger.info('Running command handler. TODO: import coastline')

        d = EsriDumper(COAST_URL)
        print(d)

        for feature in d:
            print(json.dumps(feature))

        logger.info('Got shoreline features downloaded')
