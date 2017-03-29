import logging

import boto3

from django.core.management.base import BaseCommand

from django.contrib.gis.geos import Point

from django.db.utils import IntegrityError
from django.db import transaction

from climate_data.models import City
import json

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Imports a cities.json file into the database from s3.

    cities.json is a geojson file where the features are points and have at
    minimum the following properties:

    name - city name
    admin1 - administrative name
    """

    help = 'imports a cities.json file into the database from s3'

    def add_arguments(self, parser):
        parser.add_argument('bucket', type=str)
        parser.add_argument('key', type=str)

    def handle(self, *args, **options):
        client = boto3.client('s3')
        response = client.get_object(Bucket=options['bucket'],
                                     Key=options['key'])
        byte_data = response['Body'].read()
        json_data = json.loads(byte_data.decode(encoding='utf-8'))
        cities = json_data['features']
        success = 0
        error = 0
        for city_data in cities:
            try:
                with transaction.atomic():
                    city, _ = City.objects.update_or_create(
                        name=city_data['properties']['name'],
                        admin=city_data['properties']['admin1'],
                        defaults={'geom': Point(*city_data['geometry']['coordinates'])})
                    city.population = city_data['properties']['population']
                    city.save()
                    success += 1
            except TypeError:
                logger.error('Bad item: %s', city_data)
                error += 1
            except IntegrityError:
                logger.error('Skipping %s, %s due to IntegrityError',
                             city_data['properties']['name'],
                             city_data['properties']['admin1'])
                error += 1

        logger.info('%s saved successfully', success)
        logger.info('%s skipped due to error', error)
