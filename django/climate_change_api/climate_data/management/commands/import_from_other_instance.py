import logging

from itertools import islice

from django.core.management.base import BaseCommand
from django.contrib.gis.geos import Point
from django.core.exceptions import ObjectDoesNotExist

from climate_data.models import (City, Scenario, ClimateModel,
                                 ClimateDataSource, ClimateDataCell,
                                 ClimateDataYear)

import requests

from time import time, sleep

logger = logging.getLogger('climate_data')
failure_logger = logging.getLogger('climate_data_import_failures')

MODEL_LIST_URL = 'https://{domain}/api/climate-model/'
CITY_LIST_URL = 'https://{domain}/api/city/'
CLIMATE_DATA_URL = 'https://{domain}/api/climate-data/{city_id}/{rcp}/?models={model}'

# wait this many seconds before retrying a request due to throttling
THROTTLE_WAIT_SECONDS = 20


def make_request(url, token, failures=10):
    wait = 1
    tries = 0
    data = None
    while True:
        try:
            start_time = time()
            res = requests.get(url, headers={'Authorization': 'Token {}'.format(token)})
            res.raise_for_status()
            data = res.json()
            logger.info('%s fetched in %f seconds', url, time() - start_time)
            return data
        except requests.exceptions.HTTPError as e:
            if res.status_code == 401:
                logger.critical('Check your authorization token')
            if res.status_code == 429:
                logger.info('Request for %s throttled. Trying again in %d second(s)',
                            url,
                            THROTTLE_WAIT_SECONDS)
                sleep(THROTTLE_WAIT_SECONDS)
                continue
            raise e
        except Exception as e:
            tries += 1
            if tries >= failures:
                raise e
            logger.error('Fetching %s failed. Trying again in %d second(s)', url, wait)
            sleep(wait)
            wait *= 2


def get_models(domain, token):
    """Return a list of available models from an instance of climate-change-api."""
    url = MODEL_LIST_URL.format(domain=domain)
    data = make_request(url, token)
    return [d['name'] for d in data]


def get_cities(domain, token):
    """Return an iterable of city dicts from an instance of climate-change-api."""
    url = CITY_LIST_URL.format(domain=domain)
    while url:
        data = make_request(url, token)
        for feature in data['features']:
            yield feature
        url = data['next']


def get_data(domain, token, city_id, rcp, model):
    """Get all the data for a city for a given rcp and model from a climate-change-api instance."""
    url = CLIMATE_DATA_URL.format(domain=domain, city_id=city_id, rcp=rcp, model=model)
    return make_request(url, token)


def create_models(models):
    """Create the ClimateModels given."""
    dbmodels = []
    for model in models:
            dbmodel = ClimateModel.objects.get_or_create(name=model)[0]
            dbmodels.append(dbmodel)
    return dbmodels


def import_city(citydata):
    """Create a city and if not already created, its grid cell from the city dict.

    City dict was downloaded from another instance.
    """
    try:
        city = City.objects.get(
            name=citydata['properties']['name'],
            admin=citydata['properties']['admin'],
        )
        if not city.map_cell:
            city.map_cell = import_map_cell(citydata['properties']['map_cell'])
            city.save()
        return city
    except ObjectDoesNotExist:
        logger.info('City does not exist, creating city')

        map_cell = import_map_cell(citydata['properties']['map_cell'])

        city_coordinates = citydata['geometry']['coordinates']
        return City.objects.create(
            name=citydata['properties']['name'],
            admin=citydata['properties']['admin'],
            geom=Point(*city_coordinates),
            _geog=Point(*city_coordinates),
            map_cell=map_cell,
        )


def import_map_cell(mapcelldata):
    map_cell_coordinates = mapcelldata['coordinates']
    return ClimateDataCell.objects.get_or_create(
        lon=map_cell_coordinates[0],
        lat=map_cell_coordinates[1]
    )[0]


def import_data(domain, token, remote_city_id, local_map_cell, scenario, model):
    """Import the the output of get_data into the database."""
    data = get_data(domain, token, remote_city_id, scenario, model)

    start_time = time()
    assert len(data['climate_models']) == 1
    for year, yeardata in data['data'].items():
        try:
            data_source = ClimateDataSource.objects.get(model=model,
                                                        scenario=scenario,
                                                        year=int(year))
            if data_source.import_completed:
                logger.info('Skipping already completed import for model %s scenario %s year %s',
                            model.name, scenario.name, year)
                continue

        except ObjectDoesNotExist:
            logger.debug('Creating data source for model %s scenario %s year %s',
                         model.name, scenario.name, year)
            data_source = ClimateDataSource.objects.create(model=model,
                                                           scenario=scenario,
                                                           year=int(year))
        cdy, created = ClimateDataYear.objects.get_or_create(
            map_cell=local_map_cell,
            data_source=data_source,
            defaults={
                'tasmin': yeardata['tasmin'],
                'tasmax': yeardata['tasmax'],
                'pr': yeardata['pr']
            }
        )
        if not created:
            cdy.tasmin = yeardata['tasmin']
            cdy.tasmax = yeardata['tasmax']
            cdy.pr = yeardata['pr']
            cdy.save()
    # note that the job completed successfully
    data_source.import_completed = True
    data_source.save()
    logger.info('Imported in %f s', time() - start_time)


class Command(BaseCommand):
    help = 'Downloads data from a remote instance and imports it locally'

    def add_arguments(self, parser):
        parser.add_argument('domain', type=str, help='domain name of the remote instance')
        parser.add_argument('token', type=str, help='API token for authorization')
        parser.add_argument('rcp', type=str, help='Scenario; RCP45 or RCP85')
        parser.add_argument('num_models', type=int, default=10,
                            help='max amount of models to import')
        parser.add_argument('num_cities', type=int, default=100,
                            help='max amount of cities to import')

    def handle(self, *args, **options):
        model_names = get_models(options['domain'], options['token'])
        if len(model_names) > options['num_models']:
            model_names = model_names[:options['num_models']]

        models = create_models(model_names)

        scenario = Scenario.objects.get(name=options['rcp'])

        imported_grid_cells = {model.name: [] for model in models}

        logger.info('Importing cities...')
        remote_cities = get_cities(options['domain'], options['token'])
        for city in islice(remote_cities, options['num_cities']):
            logger.info('Importing city %s, %s',
                        city['properties']['name'],
                        city['properties']['admin'])

            created_city = import_city(city)
            coordinates = (created_city.map_cell.lat, created_city.map_cell.lon)
            for model in models:
                if coordinates in imported_grid_cells[model.name]:
                    logger.info('Skipping %s, data already imported', model.name)
                    continue

                if ClimateDataYear.objects.filter(
                        data_source__model=model,
                        data_source__scenario=scenario,
                        map_cell=created_city.map_cell).exists():
                    logger.info('Skipping %s, data already imported', model.name)
                else:
                    logger.info('Importing %s', model)
                    try:
                        import_data(
                            domain=options['domain'],
                            token=options['token'],
                            remote_city_id=city['id'],
                            local_map_cell=created_city.map_cell,
                            scenario=scenario,
                            model=model)
                        imported_grid_cells[model.name].append(coordinates)
                    except Exception as ex:
                        logger.error(ex, exc_info=True)
                        logger.warn('Failed importing %s, destroying partial import', model.name)
                        ClimateDataYear.objects.filter(
                            data_source__model=model,
                            data_source__scenario=scenario,
                            map_cell=created_city.map_cell).delete()
                        failure_logger.warn('Import failed for model %s scenario %s city %s %s, %s',
                                            model.name,
                                            scenario.name,
                                            city['id'],
                                            city['properties']['name'],
                                            city['properties']['admin'])
