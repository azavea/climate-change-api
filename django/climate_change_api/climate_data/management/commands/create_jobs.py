import logging
import json

from django.core.management.base import BaseCommand
from django.conf import settings

from boto_helpers.sqs import get_queue
from climate_data.models import ClimateDataset, ClimateModel, Scenario

logger = logging.getLogger(__name__)


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

    def handle(self, *args, **options):
        queue = get_queue(QueueName=settings.SQS_QUEUE_NAME,
                          Attributes=settings.SQS_IMPORT_QUEUE_ATTRIBUTES)
        dataset = ClimateDataset.objects.get(name=options['dataset'])
        scenario_id = Scenario.objects.get(name=options['rcp']).id
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
                    'year': year
                })
