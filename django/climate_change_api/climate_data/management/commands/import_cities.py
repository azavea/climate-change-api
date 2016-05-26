import logging

import boto3

from django.core.management.base import BaseCommand

from django.contrib.gis.geos import Point

from django.db.utils import IntegrityError

from climate_data.models import City
import json

logger = logging.getLogger('django')


class Command(BaseCommand):
    help = 'imports a cities.json file into the database'

    def add_arguments(self, parser):
        parser.add_argument('bucket', type=str)
        parser.add_argument('key', type=str)

    def handle(self, *args, **options):
        FIELDS = (
            ('name', 'name'),
            ('admin1', 'admin'),
        )
        client = boto3.client('s3')
        response = client.get_object(Bucket=options['bucket'],
                                     Key=options['key'])
        cities = json.load(response['Body'])['features']
        success = 0
        error = 0
        for city_data in cities:
            try:
                city = City()
                city.geom = Point(*city_data['geometry']['coordinates'])
                for src, dest in FIELDS:
                    setattr(city, dest, city_data['properties'][src])
                city.save()
                success += 1
            except TypeError:
                logger.error('Bad item: %s', city_data)
                error += 1
            except IntegrityError:
                logger.error('Skipping %s, %s due to IntregrityError',
                             city.name, city.admin)
                error += 1

        logger.info('%s saved successfully', success)
        logger.info('%s skipped due to error', error)
