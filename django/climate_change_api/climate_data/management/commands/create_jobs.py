import logging
import json

import boto3

from django.core.management.base import BaseCommand
from django.db.utils import IntegrityError
from django.conf import settings

from climate_data.models import ClimateModel, Scenario, ClimateData, City

logger = logging.getLogger(__name__)


def send_message(queue, message):
    """Create a message in SQS with the provided body"""
    body = json.dumps(message)
    queue.send_message(MessageBody=body)
    logger.debug(body)


def get_model_id_from_name(name):
    return ClimateModel.objects.get(name=name).id


def prepopulate_rows(queue, model_id, scenario_id, vars, year):
    cities = City.objects.all()
    objects_to_create = []
    for city in cities:
        objects_to_create += [ClimateData(city=city,
                                          climate_model_id=model_id,
                                          scenario_id=scenario_id,
                                          year=int(year),
                                          day_of_year=day)
                              for day in xrange(1, 367)]
        if len(objects_to_create) > 10000:
            try:
                ClimateData.objects.bulk_create(objects_to_create)
            except IntegrityError:
                pass
            objects_to_create = []
    try:
        ClimateData.objects.bulk_create(objects_to_create)
    except IntegrityError:
        pass
    for var in vars:
        send_message(queue, {'scenario_id': scenario_id,
                             'var': var,
                             'model_id': model_id,
                             'year': year})


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
        parser.add_argument('vars', type=str,
                            help='Comma separated list of vars (of "tasmin", '
                                 '"tasmax", and "pr") or "all"')

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
        if options['vars'] == 'all':
            vars = ['tasmin', 'tasmax', 'pr']
        else:
            vars = options['vars'].split(',')
            for var in vars:
                assert var in ('tasmin', 'tasmax', 'pr')
        for year in years:
            for model_id in model_ids:
                send_message(queue, {'scenario_id': scenario_id,
                                     'vars': vars,
                                     'model_id': model_id,
                                     'year': year,
                                     'prepopulate': True})
