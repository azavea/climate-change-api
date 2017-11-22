import json
import logging

import boto3
import requests

from django.core.management.base import BaseCommand

from django.contrib.gis.geos import Point

from climate_data.models import City

logger = logging.getLogger(__name__)

GEONAMES_API_URL = 'http://api.geonames.org/getJSON'


class Command(BaseCommand):
    """Reads cities from s3 and queries geonames API to update the matching city in the database.

    Takes arguments for s3 bucket name and key (file name) for the s3 GeoJSON file of cities.
    Also takes argument for a geonames user account.

    To create a geonames user account, go here: http://www.geonames.org/login
    Enable free web service querying on the account by clicking button at bottom of account page.

    cities.json is a geojson file where the features are points and have at
    minimum the following properties:

    geonameid - unique identifier for geonames API place record
    name - city name
    admin1 - administrative name
    population - city population count
    geometry.coordinates - city location point
    """

    help = 'updates city data using geonames based on import file from s3'

    def add_arguments(self, parser):
        parser.add_argument('bucket', type=str)
        parser.add_argument('key', type=str)
        parser.add_argument('geoname_user', type=str)

    def handle(self, *args, **options):
        geoname_user = options['geoname_user']
        client = boto3.client('s3')
        response = client.get_object(Bucket=options['bucket'],
                                     Key=options['key'])
        byte_data = response['Body'].read()
        json_data = json.loads(byte_data.decode(encoding='utf-8'))
        cities = json_data['features']
        updated = 0
        for city_data in cities:
            if not city_data.get('geometry'):
                logger.error('Skipping %s, %s which has no geometry',
                             city_data['properties']['name'],
                             city_data['properties']['admin1'])
                continue

            point = Point(*city_data['geometry']['coordinates'])
            found = City.objects.filter(geom__intersects=point)
            if not found:
                logger.error('Skipping %s, %s because it was not found in the database',
                             city_data['properties']['name'],
                             city_data['properties']['admin1'])
                continue
            elif found.count() > 1:
                logger.error('Skipping %s, %s because multiple matches found in the database',
                             city_data['properties']['name'],
                             city_data['properties']['admin1'])
                continue

            db_city = found[0]
            logger.info('Found %s, %s in DB at same point as %s, %s in S3 file',
                        db_city.name,
                        db_city.admin,
                        city_data['properties']['name'],
                        city_data['properties']['admin1'])

            # Once point from s3 file has been matched to point in database,
            # can use s3 record to get the geonames ID before requesting current geonames data.
            geoname_id = city_data['properties'].get('geonameid')
            if not geoname_id:
                logger.error('Skipping %s, %s which has no geoname ID',
                             city_data['properties']['name'],
                             city_data['properties']['admin1'])

            request = requests.get(GEONAMES_API_URL, params={'geonameId': geoname_id,
                                   'username': geoname_user})

            if not request.ok:
                logger.error('Failed to query geonames for %s, %s. Got: %s: %s',
                             db_city.name,
                             db_city.admin,
                             request.status_code,
                             request.reason)
                continue

            response = request.json()

            # check if got a 200 from geonames, but query failed
            if response.get('status'):
                logger.error('Geonames query for %s, %s failed. Response: %s',
                             db_city.name,
                             db_city.admin,
                             response['status']['message'])
                continue

            name = response['name']
            admin = response['adminCode1']
            population = response['population']

            logger.info('Updating %s, %s, pop: %s to %s, %s, pop: %s',
                        db_city.name,
                        db_city.admin,
                        db_city.population,
                        name,
                        admin,
                        population)

            db_city.name = name
            db_city.admin = admin
            db_city.population = population

            db_city.save()
            updated += 1

        logger.info('%s of %s cities in the database have been updated successfully',
                    updated,
                    City.objects.count())
