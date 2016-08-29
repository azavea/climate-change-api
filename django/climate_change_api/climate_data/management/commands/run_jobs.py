import logging
import os
import json
import tempfile
import boto3

from time import sleep
from django.core.management.base import BaseCommand
from django.conf import settings
from django.db import IntegrityError

from boto_helpers.sqs import get_queue
from climate_data.models import ClimateModel, Scenario, ClimateDataSource, ClimateData
from climate_data.nex2db import Nex2DB

logger = logging.getLogger('climate_data')

BUCKET = 'nasanex'
KEY_FORMAT = ('NEX-GDDP/BCSD/{rcp}/day/atmos/{var}/r1i1p1/v1.0/'
              '{var}_day_BCSD_{rcp}_r1i1p1_{model}_{year}.nc')


def download_nc(rcp, model, year, var, dir):
    key = KEY_FORMAT.format(rcp=rcp.lower(), model=model, year=year, var=var)
    filename = os.path.join(dir, os.path.basename(key))
    s3 = boto3.resource('s3')
    s3.meta.client.download_file(BUCKET, key, filename)
    return filename


def process_message(message, queue):
    logger.debug('processing SQS message')
    # extract info from message
    message_dict = json.loads(message.body)
    logger.debug('Processing message for model {model_id} scenario {scenario_id} year {year}'.format(**message_dict))
    model = ClimateModel.objects.get(id=message_dict['model_id'])
    scenario = Scenario.objects.get(id=message_dict['scenario_id'])
    year = message_dict['year']
    logger.info('Processing SQS message for model %s scenario %s year %s',
                 model.name, scenario.name, year)

    try:
        datasource = ClimateDataSource(model=model, scenario=scenario, year=year)
        datasource.save()
    except IntegrityError:
        logger.error('Ignoring message: source already exists for model %s scenario %s year %s',
                     model.name, scenario.name, year)
        return

    # download files
    tmpdir = tempfile.mkdtemp()
    # get .nc file
    variables = {var: download_nc(scenario.name, model.name, year, var, tmpdir)
                 for var in ClimateData.VARIABLE_CHOICES}
    assert(all(variables))

    # pass to nex2db
    try:
        Nex2DB().nex2db(variables, datasource)
    except:
        logger.exception("Failed to process data for model %s scenario %s year %s",
                         model.name, scenario.name, year)
        raise
    finally:
        # Success or failure, clean up the .nc files
        for path in variables.values():
            os.unlink(path)

    logger.debug('SQS message processed')


class Command(BaseCommand):
    """Processes jobs from SQS to extract data from NASA NEX NetCDF files

    Processes messages with the following format:
    {"scenario_id": 1, "model_id": 1, "year": "2016"}

    """

    help = 'Processes jobs from SQS to extract data from NASA NEX NetCDF files'

    def handle(self, *args, **options):
        logger.info('Starting job processing...')
        queue = get_queue(QueueName=settings.SQS_QUEUE_NAME,
                          Attributes=settings.SQS_IMPORT_QUEUE_ATTRIBUTES)
        failures = 0
        while failures < 10:
            try:
                while True:
                    message = queue.receive_messages()[0]
                    process_message(message, queue)
                    message.delete()
                    failures = 0
            except IndexError:
                logger.debug("Empty queue, waiting 10 seconds...")
                sleep(10)
                failures += 1
        logger.info('Finished processing jobs')
