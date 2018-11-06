import logging

from esridump.dumper import EsriDumper

from django.core.management.base import BaseCommand

from django.contrib.gis.geos import GEOSGeometry, LineString, MultiPolygon
from django.db import connection

from climate_data.models import ClimateDataCell, Coastline

logger = logging.getLogger(__name__)


# ArcGIS server hosting NOAA coastline data
COAST_URL = 'https://encdirect.noaa.gov/arcgis/rest/services/encdirect/enc_coastal/MapServer/70'
COASTAL_SRID = 4326

RAW_UNION = """
SELECT ST_Union(polygons.poly) AS geom FROM (
    SELECT
        coast.objectid,
        ST_CollectionExtract(ST_ConcaveHull(ST_Buffer(
        ST_Collect(coast.geom)::geography, 4000)::geometry, 0.99, true), 3) AS poly
    FROM (
        SELECT objectid, (ST_Dump(geom)).geom AS geom
        FROM climate_data_coastline) AS coast
        GROUP BY objectid)
AS polygons;
"""


class Command(BaseCommand):
    """Imports coast outline from NOAA. Sets `is_coastal` on `City`.

    Unions together coastline LineString geometries, buffers them to ~2.5 miles (4000 meters),
    then flags cities with boundaries that intersect with the resulting MultiPolygon as coastal.
    """

    def handle(self, *args, **options):
        logger.info('Running NOAA coastline import')

        dumper = EsriDumper(COAST_URL)

        for feature in dumper:
            object_id = feature['properties']['OBJECTID']
            line_string = LineString(feature['geometry']['coordinates'],
                                     srid=COASTAL_SRID)

            Coastline.objects.update_or_create(objectid=object_id, defaults={'geom': line_string})
            logger.debug('Loaded coastline LineString: %s', object_id)

        logger.info('Got shoreline features downloaded; going to match to city bounds')

        # set is_coastal flag on cities with bounds that intersect the bufferred coastal area
        with connection.cursor() as cursor:
            cursor.execute(RAW_UNION)
            row = cursor.fetchone()
            poly = MultiPolygon(*GEOSGeometry(row[0]))

            coastal_cells = ClimateDataCell.objects.filter(geom__within=poly)
            count_coastal_cells = coastal_cells.update(is_coastal=True)
            total_coastal_cells = ClimateDataCell.objects.count()
            logger.info('Flagged %s of %s ClimateDataCells as coastal',
                        count_coastal_cells, total_coastal_cells)
