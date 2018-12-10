import logging
import json

from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.core.validators import URLValidator
from django.conf import settings

from boto_helpers.sqs import get_queue
from climate_data.models import ClimateDataset, ClimateModel, Scenario

logger = logging.getLogger(__name__)


def validate_url(url):
    validator = URLValidator(schemes=['http', 'https'])
    try:
        validator(url)
    except ValidationError:
        raise CommandError('{} is not a valid URL!'.format(url))


def send_message(queue, message):
    """Create a message in SQS with the provided body."""
    body = json.dumps(message)
    queue.send_message(MessageBody=body)
    logger.debug(body)


def get_model_id_from_name(name):
    return ClimateModel.objects.get(name=name).id


class Command(BaseCommand):
    """Creates jobs on SQS to extract data from NASA NEX NetCDF files.

    Creates messages with the following format:
    {"dataset": "NEX-GDDP", "model_id": 1, "scenario_id": 1, "year": "2016"}

    where "model_id" and "scenario_id" are Climate API database ids for the
    given model and scenario.
    """

    help = 'Creates jobs on SQS to extract data from NASA NEX NetCDF files'

    def add_arguments(self, parser):
        parser.add_argument('dataset', type=str,
                            help='Name of the climate dataset to import')
        parser.add_argument('rcp', type=str,
                            help='Name of climate emissions scenario to match '
                                 'name in database')
        parser.add_argument('models', type=str,
                            help='Comma separated list of models, or "all"')
        parser.add_argument('years', type=str,
                            help='Comma separated list of years, or "all"')
        parser.add_argument('--update-existing', action='store_true',
                            help='If provided, jobs will update existing city data')
        parser.add_argument('--import-boundary-url', type=str,
                            help='A URL to a zipped (multi)polygon shapefile to filter the ' +
                                 'import by. All climate data cells that intersect this ' +
                                 'boundary will imported. This option takes precedence over ' +
                                 '--import-geojson-url')
        parser.add_argument('--import-geojson-url', type=str,
                            help='A URL to a geojson FeatureCollection of Point features. ' +
                                 'The importer will import climate data for each ' +
                                 'point feature in the FeatureCollection.')

    def handle(self, *args, **options):
        queue = get_queue(QueueName=settings.SQS_QUEUE_NAME,
                          Attributes=settings.SQS_IMPORT_QUEUE_ATTRIBUTES)
        dataset = ClimateDataset.objects.get(name=options['dataset'])
        scenario_id = Scenario.objects.get(name=options['rcp']).id
        update_existing = options['update_existing']
        import_boundary_url = options.get('import_boundary_url', None)
        import_geojson_url = options.get('import_geojson_url', None)
        if import_boundary_url and import_geojson_url:
            raise CommandError('You must choose one of import_boundary_url or import_geojson_url.')
        if import_boundary_url:
            validate_url(import_boundary_url)
        if import_geojson_url:
            validate_url(import_geojson_url)

        if options['models'] == 'all':
            model_ids = [m.id for m in dataset.models.all()]
        else:
            model_ids = list(map(get_model_id_from_name, options['models'].split(',')))
        if options['years'] == 'all':
            years = list((map(str, range(1950, 2006)) if options['rcp'] == 'historical'
                         else map(str, range(2006, 2101))))
        else:
            years = options['years'].split(',')
        for year in years:
            for model_id in model_ids:
                send_message(queue, {
                    'dataset': dataset.name,
                    'scenario_id': scenario_id,
                    'model_id': model_id,
                    'year': year,
                    'import_boundary_url': import_boundary_url,
                    'import_geojson_url': import_geojson_url,
                    'update_existing': update_existing,
                })
