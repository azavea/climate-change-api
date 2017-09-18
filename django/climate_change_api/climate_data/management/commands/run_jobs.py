import json
import logging
import os
import shutil
import tempfile
from time import sleep

import boto3
from boto_helpers.sqs import get_queue

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand

from climate_data.models import (ClimateDataset,
                                 ClimateDataSource,
                                 ClimateDataYear,
                                 Scenario)
from climate_data.nex2db import Nex2DB

logger = logging.getLogger('climate_data')
failure_logger = logging.getLogger('climate_data_import_failures')

BUCKET = 'nasanex'


def get_key_format_for_dataset(dataset_name):
    if dataset_name == 'NEX-GDDP':
        return ('NEX-GDDP/BCSD/{rcp}/day/atmos/{var}/{ensemble}/v1.0/'
                '{var}_day_BCSD_{rcp}_{ensemble}_{model}_{year}.nc')
    elif dataset_name == 'LOCA':
        return ('LOCA/{model}/16th/{rcp}/{ensemble}/{var}/'
                '{var}_day_{model}_{rcp}_{ensemble}_{year}0101-{year}1231.LOCA_2016-04-02.16th.nc')
    else:
        raise ValueError('Unsupported dataset {}'.format(dataset_name))


def get_gddp_model_ensemble(model_name, rcp):
    return 'r1i1p1'


def get_loca_model_ensemble(model_name, rcp):
    """Return ensemble given LOCA model and scenario."""
    ensembles = {
        'historical': {
            'CCSM4': 'r6i1p1',
            'GISS-E2-H': 'r6i1p1',
            'GISS-E2-R': 'r6i1p1',
        },
        'RCP45': {
            'CCSM4': 'r6i1p1',
            'EC-EARTH': 'r8i1p1',
            'GISS-E2-H': 'r6i1p3',
            'GISS-E2-R': 'r6i1p1'
        },
        'RCP85': {
            'CCSM4': 'r6i1p1',
            'EC-EARTH': 'r2i1p1',
            'GISS-E2-H': 'r2i1p1',
            'GISS-E2-R': 'r2i1p1'
        }
    }
    try:
        return ensembles[rcp][model_name]
    except KeyError:
        return 'r1i1p1'


def get_dataset_model_ensemble(dataset_name, model_name, rcp):
    return {
        'LOCA': get_loca_model_ensemble,
        'NEX-GDDP': get_gddp_model_ensemble
    }[dataset_name](model_name, rcp)


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


def download_nc(dataset_name, rcp, model, year, var, dir):
    ensemble = get_dataset_model_ensemble(dataset_name, model, rcp)
    key_format = get_key_format_for_dataset(dataset_name)
    key = key_format.format(rcp=rcp.lower(), model=model, year=year, var=var, ensemble=ensemble)
    filename = os.path.join(dir, os.path.basename(key))
    s3 = boto3.resource('s3')
    logger.warning('Downloading file: s3://{}/{}'.format(BUCKET, key))
    s3.meta.client.download_file(BUCKET, key, filename)
    return filename


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
    logger.info('Processing SQS message for model %s scenario %s year %s',
                model.name, scenario.name, year)

    try:
        datasource = ClimateDataSource.objects.get(dataset=dataset,
                                                   model=model,
                                                   scenario=scenario,
                                                   year=year)
        if datasource.import_completed:
            logger.info('Skipping already completed import for '
                        'dataset %s model %s scenario %s year %s',
                        dataset.name, model.name, scenario.name, year)
            logger.debug('SQS message processed')
            return
        else:
            # Log note but still continue to attempt re-import
            logger.warn('Found incomplete import for dataset %s model %s scenario %s year %s',
                        dataset.name, model.name, scenario.name, year)
    except ObjectDoesNotExist:
        logger.debug('Creating data source for dataset %s model %s scenario %s year %s',
                     dataset.name, model.name, scenario.name, year)
        datasource = ClimateDataSource.objects.create(dataset=dataset,
                                                      model=model,
                                                      scenario=scenario,
                                                      year=year)

    # download files
    tmpdir = tempfile.mkdtemp()
    try:
        # get .nc file
        variables = {var: download_nc(dataset.name, scenario.name, model.name, year, var, tmpdir)
                     for var in ClimateDataYear.VARIABLE_CHOICES}
        assert(all(variables))

        # pass to nex2db
        Nex2DB(logger=logger).nex2db(variables, datasource)
    except:
        logger.exception('Failed to process data for dataset %s model %s scenario %s year %s',
                         dataset.name, model.name, scenario.name, year)
        failure_logger.exception('Failed to process data for '
                                 'dataset %s model %s scenario %s year %s',
                                 dataset.name, model.name, scenario.name, year)
        raise
    finally:
        # Success or failure, clean up the .nc files
        shutil.rmtree(tmpdir)

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
