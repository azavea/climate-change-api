import logging
import json

import boto3

from django.core.management.base import BaseCommand
from django.conf import settings

from climate_data.models import ClimateModel, Scenario

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
        parser.add_argument('rcp', type=str,
                            help='Name of climate emmisions scenario to match '
                                 'name in database')
        parser.add_argument('models', type=str,
                            help='Comma separated list of models, or "all"')
        parser.add_argument('years', type=str,
                            help='Comma separated list of years, or "all"')

    def handle(self, *args, **options):
        sqs = boto3.resource('sqs')
        queue = sqs.get_queue_by_name(QueueName=settings.SQS_QUEUE_NAME)
        scenario_id = Scenario.objects.get(name=options['rcp']).id
        if options['models'] == 'all':
            model_ids = map(lambda m: m.id, list(ClimateModel.objects.all()))
        else:
            model_ids = map(get_model_id_from_name, options['models'].split(','))
        if options['years'] == 'all':
            years = map(str, range(2006, 2100))
        else:
            years = options['years'].split(',')
        for year in years:
            for model_id in model_ids:
                send_message(queue, {'scenario_id': scenario_id,
                                     'model_id': model_id,
                                     'year': year})
