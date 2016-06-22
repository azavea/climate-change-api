import logging
import os
import json
import tempfile
import boto3

from time import sleep
from django.core.management.base import BaseCommand
from django.conf import settings

from climate_data.models import ClimateModel, Scenario
from climate_data import nex2db

from climate_data.management.commands.create_jobs import prepopulate_rows

logger = logging.getLogger(__name__)

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
    # extract info from message
    message_dict = json.loads(message.body)
    model = ClimateModel.objects.get(id=message_dict['model_id'])
    scenario = Scenario.objects.get(id=message_dict['scenario_id'])
    year = message_dict['year']
    if 'prepopulate' in message_dict:
        prepopulate_rows(queue, model.id, scenario.id, message_dict['vars'], year)
        return
    var = message_dict['var']
    tmpdir = tempfile.mkdtemp()
    # get .nc file
    filename = download_nc(scenario.name, model.name, year, var, tmpdir)
    # pass to nex2db
    nex2db.nex2db(filename, var, scenario, model, model.base_time)
    # delete .nc file
    os.unlink(filename)


class Command(BaseCommand):
    """Processes jobs from SQS to extract data from NASA NEX NetCDF files

    Processes messages with the following format:
    {"scenario_id": 1, "var": "tasmin", "model_id": 1, "year": "2016"}

    """

    help = 'Processes jobs from SQS to extract data from NASA NEX NetCDF files'

    def handle(self, *args, **options):
        sqs = boto3.resource('sqs')
        queue = sqs.get_queue_by_name(QueueName=settings.SQS_QUEUE_NAME)
        failures = 0
        while failures < 10:
            try:
                while True:
                    message = queue.receive_messages()[0]
                    process_message(message, queue)
                    message.delete()
                    failures = 0
            except:
                sleep(10)
                failures += 1
