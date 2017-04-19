import logging
from time import sleep

from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError

from climate_data.models import City, CityBoundary
from climate_data.geo_boundary.exceptions import GeoBoundaryError

logger = logging.getLogger(__name__)


class Command(BaseCommand):

    help = 'Imports geographic boundaries for cities in the database'

    def add_arguments(self, parser):
        parser.add_argument('--overwrite', action='store_true',
                            help='If provided, cities with existing boundaries will overwritten')
        parser.add_argument('--limit', type=int, help='Limit updates to this number of cities')
        parser.add_argument('--offset', type=int, default=0,
                            help='Start updates at the specified offset')
        parser.add_argument('--interval', type=float, default=0.5,
                            help='Interval in seconds to sleep between boundary import operations')

    def handle(self, *args, **options):

        if not City.objects.all().exists():
            raise CommandError('No cities found. Must first run the `import_cities` command.')

        limit = options['limit']
        offset = options['offset']

        queryset = City.objects.all()
        if not options['overwrite']:
            logger.info('Skipping cities with existing boundary. Use --overwrite to re-import ' +
                        'all boundaries.')
            queryset = queryset.filter(boundary__isnull=True)
        if limit is not None:
            queryset = queryset[offset:offset + limit]
        else:
            queryset = queryset[offset:]

        success = 0
        total = 0
        for city in queryset:
            try:
                CityBoundary.objects.create_for_city(city)
                logger.info('Created boundary for city: %s, %s', city.name, city.admin)
                success += 1
                # Short sleep to avoid hammering the boundary APIs
                sleep(options['interval'])
            except (ValidationError, GeoBoundaryError) as e:
                logger.warning(e)
            total += 1

        logger.info('%s of %s city boundaries imported successfully', success, total)
