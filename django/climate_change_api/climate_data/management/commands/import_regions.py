from contextlib import contextmanager
import gc
import logging
import json

import boto3

from django.core.management.base import BaseCommand

from climate_data.models import City, Region
from django.contrib.gis.geos import GEOSGeometry, MultiPolygon


logger = logging.getLogger(__name__)


@contextmanager
def get_features_from_response(response):
    """Yield json features via context manager from a boto3 StreamingResponse."""
    byte_data = response['Body'].read()
    features = json.loads(byte_data.decode(encoding='utf-8'))['features']
    yield features
    del features
    del byte_data
    gc.collect()


class Command(BaseCommand):
    """Imports a ecoregions.geojson file into the database from s3.

    ecoregions.geojson is a geojson file where the features have
    at minimum the following properties:

    NA_L1CODE
    NA_L1NAME
    NA_L2CODE
    NA_L2NAME
    """

    help = ('Imports an ecoregions.geojson file into the database from s3. '
            'If bucket and key not specifed, will associate cities with '
            'regions only')

    def add_arguments(self, parser):
        parser.add_argument('--bucket', type=str)
        parser.add_argument('--key', type=str)

    def handle(self, *args, **options):
        if options['bucket'] and options['key']:
            print('Pulling geojson from s3 bucket...')
            client = boto3.client('s3')
            response = client.get_object(Bucket=options['bucket'],
                                         Key=options['key'])
            with get_features_from_response(response) as features:
                print('Loading data...')
                data = {}
                for feature in features:
                    l1, l2 = [int(val) for val in feature['properties']['NA_L2CODE'].split('.')]
                    if (l1, l2) in data:
                        data[(l1, l2)]['geom'].append(json.dumps(feature['geometry']))
                    else:
                        data[(l1, l2)] = {
                            'level1': l1,
                            'level1_description': feature['properties']['NA_L1NAME'],
                            'level2': l2,
                            'level2_description': feature['properties']['NA_L2NAME'],
                            'geom': [json.dumps(feature['geometry'])]
                        }

            for region in data.values():
                geom = MultiPolygon(*(GEOSGeometry(x) for x in region['geom'])).simplify(0.001)
                region['geom'] = geom
                Region.objects.update_or_create(level1=region['level1'],
                                                level2=region['level2'],
                                                defaults=region)
                print('Loaded {}, {}'.format(region['level1_description'],
                                             region['level2_description']))

        for city in City.objects.all():
            try:
                city.region = Region.objects.get(geom__covers=city.geom)
                logger.info('Assigning %s, %s to %d.%d %s, %s',
                            city.name,
                            city.admin,
                            city.region.level1,
                            city.region.level2,
                            city.region.level1_description,
                            city.region.level2_description)
                city.save()
            except Region.DoesNotExist:
                logger.error("Can't assign region to city %s, %s",
                             city.name, city.admin)
