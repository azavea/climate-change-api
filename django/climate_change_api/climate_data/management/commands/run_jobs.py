import json
import logging
from time import sleep

from boto_helpers.sqs import get_queue

from django.conf import settings
from django.core.management.base import BaseCommand

from climate_data.models import (ClimateDataset,
                                 ClimateDataSource,
                                 ClimateDataYear,
                                 Scenario)
from climate_data.nex2db import Nex2DB

logger = logging.getLogger('climate_data')
failure_logger = logging.getLogger('climate_data_import_failures')

def handle_failing_message(message, failures):
    message_dict = json.loads(message.body)
    key = '{dataset}-{model_id}-{scenario_id}-{year}'.format(**message_dict)
    label = 'Message ID {} for dataset {dataset} model id {model_id} scenario id {scenario_id} '\
            'year {year}'.format(message.message_id, **message_dict)
    failures[key] = failures.get(key, 0) + 1

    warn_text = '{} failed {} time(s)'.format(label, failures[key])

    logger.warn(warn_text)

    if failures[key] > settings.SQS_MAX_RETRIES:
        error_text = '{} failed more than {} times, giving up.'\
                     .format(label, settings.SQS_MAX_RETRIES)
        logger.error(error_text, exc_info=True)
        failure_logger.error(error_text)

        message.delete()

    else:
        # Re-place message in the queue by making it instantly visible
        # See http://boto3.readthedocs.io/en/latest/reference/services/sqs.html#SQS.Message.change_visibility  # NOQA: E501
        message.change_visibility(VisibilityTimeout=0)


def process_message(message, queue):
    logger.debug('processing SQS message')
    # extract info from message
    message_dict = json.loads(message.body)
    logger.debug('Processing message for dataset {dataset} model {model_id} scenario '
                 '{scenario_id} year {year}'
                 .format(**message_dict))
    dataset = ClimateDataset.objects.get(name=message_dict['dataset'])
    model = dataset.models.get(id=message_dict['model_id'])
    scenario = Scenario.objects.get(id=message_dict['scenario_id'])
    year = message_dict['year']
    update_existing = message_dict.get('update_existing', False)
    logger.info('Processing SQS message for model %s scenario %s year %s',
                model.name, scenario.name, year)

    # download files
    try:
        importer = Nex2DB(
            dataset,
            scenario,
            model,
            year,
            update_existing=update_existing,
            logger=logger)
        importer.import_netcdf_data()
    except Exception:
        logger.exception('Failed to process data for dataset %s model %s scenario %s year %s',
                         dataset.name, model.name, scenario.name, year)
        failure_logger.exception('Failed to process data for '
                                 'dataset %s model %s scenario %s year %s',
                                 dataset.name, model.name, scenario.name, year)
        raise

    logger.debug('SQS message processed')


class Command(BaseCommand):
    """Processes jobs from SQS to extract data from NASA NEX NetCDF files.

    Processes messages with the following format:
    {"dataset": NEX-GDDP, "scenario_id": 1, "model_id": 1, "year": "2016"}
    """

    help = 'Processes jobs from SQS to extract data from NASA NEX NetCDF files'

    def handle(self, *args, **options):
        logger.info('Starting job processing...')
        queue = get_queue(QueueName=settings.SQS_QUEUE_NAME,
                          Attributes=settings.SQS_IMPORT_QUEUE_ATTRIBUTES)
        queue_failures = 0
        message_failures = {}
        while queue_failures < 10:
            try:
                while True:
                    message = queue.receive_messages()[0]
                    try:
                        process_message(message, queue)
                        message.delete()
                        queue_failures = 0
                    except Exception:
                        handle_failing_message(message, message_failures)
            except IndexError:
                logger.debug('Empty queue, waiting 10 seconds...')
                sleep(10)
                queue_failures += 1

        logger.info('Finished processing jobs')
