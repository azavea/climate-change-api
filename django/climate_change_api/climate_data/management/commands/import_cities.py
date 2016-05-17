from pprint import pprint

from django.core.management.base import BaseCommand, CommandError

from django.contrib.gis.geos import Point

from django.db.utils import IntegrityError

from climate_data.models import City
import json


class Command(BaseCommand):
    help = 'imports a cities.json file into the database'

    def add_arguments(self, parser):
        parser.add_argument('filename', type=str)

    def handle(self, *args, **options):
        FIELDS = (
            ('name', 'name'),
            ('admin1', 'admin'),
        )
        with open(options['filename'], 'r') as f:
            cities = json.load(f)['features']
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
                print('Bad item:')
                pprint(city_data)
                error += 1
            except IntegrityError:
                print('Skipping {}, {} due to IntregrityError'
                      .format(city.name, city.admin))
                error += 1

        print('{} saved successfully'.format(success))
        print('{} skipped due to error'.format(error))
