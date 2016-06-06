import logging
import json

import boto3

from django.core.management.base import BaseCommand
from django.conf import settings

from climate_data.models import ClimateModel

logger = logging.getLogger(__name__)


def send_message(queue, message):
    """Create a message in SQS with the provided body"""
    body = json.dumps(message)
    queue.send_message(MessageBody=body)
    logger.debug(body)


def get_model_id_from_name(name):
    return ClimateModel.objects.get(name=name).id


class Command(BaseCommand):
    """Creates jobs on SQS to extract data from NASA NEX NetCDF files

    Creates messages with the following format:
    {"var": "tasmin", "model": 1, "year": "2016"}

    where "model" is the database id of the model
    """

    help = 'Creates jobs on SQS to extract data from NASA NEX NetCDF files'

    def add_arguments(self, parser):
        parser.add_argument('models', type=str,
                            help='Comma separated list of models, or "all"')
        parser.add_argument('years', type=str,
                            help='Comma separated list of years, or "all"')
        parser.add_argument('vars', type=str,
                            help='Comma separated list of vars (of "tasmin", '
                                 '"tasmax", and "pr") or "all"')

    def handle(self, *args, **options):
        sqs = boto3.resource('sqs')
        queue = sqs.get_queue_by_name(QueueName=settings.SQS_QUEUE_NAME)
        if options['models'] == 'all':
            models = map(lambda m: m.id, list(ClimateModel.objects.all()))
        else:
            models = map(get_model_id_from_name, options['models'].split(','))
        if options['years'] == 'all':
            years = map(str, range(2006, 2100))
        else:
            years = options['years'].split(',')
        if options['vars'] == 'all':
            vars = ['tasmin', 'tasmax', 'pr']
        else:
            vars = options['vars'].split(',')

        for var in vars:
            for model in models:
                for year in years:
                    send_message(queue, {'var': var, 'model': model, 'year': year})
