import logging

from itertools import islice

from django.core.management.base import BaseCommand
from django.contrib.gis.geos import Point
from django.core.exceptions import ObjectDoesNotExist

from climate_data.models import (City,
                                 Scenario,
                                 ClimateModel,
                                 ClimateDataSource,
                                 ClimateDataCell,
                                 ClimateDataCityCell,
                                 ClimateDataYear,
                                 ClimateDataset)

import requests

from time import time, sleep

logger = logging.getLogger('climate_data')
failure_logger = logging.getLogger('climate_data_import_failures')

MODEL_LIST_URL = 'https://{domain}/api/climate-model/'
CITY_LIST_URL = 'https://{domain}/api/city/'
CLIMATE_DATA_URL = ('https://{domain}/api/climate-data/{city_id}/{rcp}/'
                    '?models={model}&dataset={dataset}')
MAP_CELL_URL = 'https://{domain}/api/city/{city_id}/map-cell/{dataset}/'

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


def get_models(domain, token, dataset):
    """Return a list of available models from an instance of climate-change-api."""
    url = MODEL_LIST_URL.format(domain=domain)
    data = make_request(url, token)
    return [d['name'] for d in data if dataset.name in d['datasets']]


def get_cities(domain, token):
    """Return an iterable of city dicts from an instance of climate-change-api."""
    url = CITY_LIST_URL.format(domain=domain)
    while url:
        data = make_request(url, token)
        for feature in data['features']:
            yield feature
        url = data['next']


def get_data(domain, token, city_id, scenario, model, dataset):
    """Get all the data for a city for a given source from a climate-change-api instance."""
    url = CLIMATE_DATA_URL.format(
        domain=domain,
        city_id=city_id,
        rcp=scenario.name,
        model=model,
        dataset=dataset.name
    )
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
    except ObjectDoesNotExist:
        logger.info('City does not exist, creating city')

        city_coordinates = citydata['geometry']['coordinates']
        city = City.objects.create(
            name=citydata['properties']['name'],
            admin=citydata['properties']['admin'],
            geom=Point(*city_coordinates),
            _geog=Point(*city_coordinates)
        )

    return city


def import_city_map_cell(domain, token, remote_city_id, dataset):
    url = MAP_CELL_URL.format(
        domain=domain,
        city_id=remote_city_id,
        dataset=dataset.name
    )
    mapcelldata = make_request(url, token)

    map_cell_coordinates = mapcelldata['geometry']['coordinates']
    return ClimateDataCell.objects.get_or_create(
        lon=map_cell_coordinates[0],
        lat=map_cell_coordinates[1]
    )[0]


def import_data(domain, token, remote_city_id, local_map_cell, scenario, model, dataset):
    """Import the the output of get_data into the database."""
    data = get_data(domain, token, remote_city_id, scenario, model, dataset)

    start_time = time()
    assert len(data['climate_models']) == 1
    for year, yeardata in data['data'].items():

        data_source, created = ClimateDataSource.objects.get_or_create(
            model=model,
            scenario=scenario,
            year=int(year),
            dataset=dataset
        )
        if created:
            logger.debug('Created data source for model %s scenario %s year %s in %s',
                         model.name, scenario.name, year, dataset.name)
        elif data_source.import_completed:
            logger.info('Skipping already completed import for model %s scenario %s year %s in %s',
                        model.name, scenario.name, year, dataset.name)
            continue

        # Ensure we received the data we expected
        assert set(yeardata.keys()) == set(['pr', 'tasmax', 'tasmin'])
        ClimateDataYear.objects.update_or_create(
            yeardata,
            map_cell=local_map_cell,
            data_source=data_source
        )
    # note that the job completed successfully
    data_source.import_completed = True
    data_source.save()
    logger.info('Imported in %f s', time() - start_time)


class Command(BaseCommand):
    help = 'Downloads data from a remote instance and imports it locally'

    def add_arguments(self, parser):
        parser.add_argument('domain', type=str, help='domain name of the remote instance')
        parser.add_argument('token', type=str, help='API token for authorization')
        parser.add_argument('dataset', type=str, help='Dataset; NEX-GDDP or LOCA')
        parser.add_argument('rcp', type=str, help='Scenario; RCP45 or RCP85')
        parser.add_argument('num_models', type=int, default=10,
                            help='max amount of models to import')
        parser.add_argument('num_cities', type=int, default=100,
                            help='max amount of cities to import')

    def handle(self, *args, **options):
        dataset = ClimateDataset.objects.get(name=options['dataset'])

        model_names = get_models(options['domain'], options['token'], dataset)
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

            try:
                map_cell = created_city.get_map_cell(dataset=dataset)
            except ObjectDoesNotExist:
                map_cell = import_city_map_cell(options['domain'], options['token'],
                                                city['id'], dataset)
                ClimateDataCityCell.objects.create(
                    city=created_city,
                    map_cell=map_cell,
                    dataset=dataset
                )

            coordinates = (map_cell.lat, map_cell.lon)
            for model in models:
                if coordinates in imported_grid_cells[model.name]:
                    logger.info('Skipping %s, data already imported', model.name)
                    continue

                if ClimateDataYear.objects.filter(
                        data_source__model=model,
                        data_source__scenario=scenario,
                        map_cell=map_cell).exists():
                    logger.info('Skipping %s, data already imported', model.name)
                else:
                    logger.info('Importing %s', model)
                    try:
                        import_data(
                            domain=options['domain'],
                            token=options['token'],
                            remote_city_id=city['id'],
                            local_map_cell=map_cell,
                            dataset=dataset,
                            scenario=scenario,
                            model=model)
                        imported_grid_cells[model.name].append(coordinates)
                    except Exception as ex:
                        logger.error(ex, exc_info=True)
                        logger.warn('Failed importing %s, destroying partial import', model.name)
                        ClimateDataYear.objects.filter(
                            data_source__model=model,
                            data_source__scenario=scenario,
                            map_cell=map_cell).delete()
                        failure_logger.warn('Import failed for model %s scenario %s city %s %s, %s',
                                            model.name,
                                            scenario.name,
                                            city['id'],
                                            city['properties']['name'],
                                            city['properties']['admin'])
