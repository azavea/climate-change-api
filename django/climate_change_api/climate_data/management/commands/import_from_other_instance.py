import logging

from itertools import islice

from django.core.management.base import BaseCommand
from django.contrib.gis.geos import Point
from django.core.exceptions import ObjectDoesNotExist

from climate_data.models import (City, Scenario, ClimateModel,
                                 ClimateDataSource, ClimateDataCell,
                                 ClimateData)

import requests
from decimal import Decimal

from time import time, sleep
from django.db import connection

logger = logging.getLogger('climate_data')

MODEL_LIST_URL = 'https://{domain}/api/climate-model/'
CITY_LIST_URL = 'https://{domain}/api/city/'
CLIMATE_DATA_URL = 'https://{domain}/api/climate-data/{city_id}/{rcp}/?models={model}'


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
            logger.info('%s fetched in %f seconds', url, time()-start_time)
            return data
        except requests.exceptions.HTTPError as e:
            if res.status_code == 401:
                logger.critical('Check your authorization token')
                raise e
        except Exception as e:
            tries += 1
            if tries >= failures:
                raise e
            logger.error('Fetching %s failed. Trying again in %d second(s)', url, wait)
            sleep(wait)
            wait *= 2


def get_models(domain, token):
    """
    Returns a list of available models from an instance of climate-change-api
    """
    url = MODEL_LIST_URL.format(domain=domain)
    data = make_request(url, token)
    return map(lambda d: d['name'], data)


def get_cities(domain, token):
    """
    Returns an iterable of city dicts from an instance of climate-change-api
    """
    url = CITY_LIST_URL.format(domain=domain)
    while url:
        data = make_request(url, token)
        for feature in data['features']:
            yield feature
        url = data['next']


def get_data(domain, token, city_id, rcp, model):
    """
    Gets all the data for a city for a given rcp and model from a climate-change-api instance
    """
    url = CLIMATE_DATA_URL.format(domain=domain, city_id=city_id, rcp=rcp, model=model)
    return make_request(url, token)


def create_models(models):
    """
    Create the ClimateModels given
    """
    dbmodels = []
    for model in models:
            dbmodel = ClimateModel.objects.get_or_create(name=model)[0]
            dbmodels.append(dbmodel)
    return dbmodels

def import_city(citydata):
    """
    Create a city and if not already created, its grid cell from the city dict
    downloaded from another instance
    """

    try:
        return City.objects.get(
            name=citydata['properties']['name'],
            admin=citydata['properties']['admin'],
        )
    except ObjectDoesNotExist:
        logger.info("City does not exist, creating city")

        map_cell_coordinates = citydata['properties']['map_cell']['coordinates']
        map_cell = ClimateDataCell.objects.get_or_create(
            lon=map_cell_coordinates[0],
            lat=map_cell_coordinates[1]
        )[0]

        city_coordinates = citydata['geometry']['coordinates']
        return City.objects.create(
            name=citydata['properties']['name'],
            admin=citydata['properties']['admin'],
            geom=Point(*city_coordinates),
            _geog=Point(*city_coordinates),
            map_cell=map_cell,
        )


def import_data(domain, token, remote_city_id, local_map_cell, scenario, model):
    """
    Import the the output of get_data into the database
    """
    data = get_data(domain, token, remote_city_id, scenario, model)

    start_time = time()
    assert len(data['climate_models']) == 1
    for year, yeardata in data['data'].iteritems():
        data_source = ClimateDataSource.objects.get_or_create(model=model,
                                                              scenario=scenario,
                                                              year=int(year))[0]
        ClimateData.objects.bulk_create([
            ClimateData(map_cell=local_map_cell,
                        data_source=data_source,
                        day_of_year=day,
                        tasmin=tasmin,
                        tasmax=tasmax,
                        pr=pr)
            for day, (tasmin, tasmax, pr) in enumerate(zip(yeardata['tasmin'],
                                                           yeardata['tasmax'],
                                                           yeardata['pr']), start=1)])
    logger.info('Imported in %f s', time() - start_time)


def get_imported_grid_cells(models):
    imported_grid_cells = {model.name: [] for model in models}

    logger.info("Checking existing data...")
    query = """
        SELECT
            climate_data_climatedatacell.lat AS lat,
            climate_data_climatedatacell.lon AS lon,
            climate_data_climatemodel.name AS model_name
        FROM climate_data_climatedata
        JOIN climate_data_climatedatacell
            ON climate_data_climatedata.map_cell_id = climate_data_climatedatacell.id
        JOIN climate_data_climatedatasource
            ON climate_data_climatedata.data_source_id = climate_data_climatedatasource.id
        JOIN climate_data_climatemodel
            ON climate_data_climatedatasource.model_id = climate_data_climatemodel.id
        WHERE climate_data_climatemodel.name = ANY(%s)
        GROUP BY climate_data_climatedatacell.id, climate_data_climatemodel.id;
    """

    with connection.cursor() as cursor:
        cursor.execute(query, [[model.name for model in models]])

        columns = [col[0] for col in cursor.description]
        for row in cursor.fetchall():
            pair = dict(zip(columns, row))
            model = pair['model_name']
            cell_modelcoordinates = (pair['lat'], pair['lon'])
            imported_grid_cells[model].append(cell_modelcoordinates)

        return imported_grid_cells


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

        imported_grid_cells = get_imported_grid_cells(models)

        logger.info("Importing cities...")
        remote_cities = get_cities(options['domain'], options['token'])
        for city in islice(remote_cities, options['num_cities']):
            logger.info('Importing city %s, %s',
                        city['properties']['name'],
                        city['properties']['admin'])

            created_city = import_city(city)
            coordinates = (created_city.map_cell.lat, created_city.map_cell.lon)
            for model in models:
                if coordinates in imported_grid_cells[model.name]:
                    logger.info("Skipping %s, data already imported", model.name)
                    continue

                if ClimateData.objects.filter(
                        data_source__model=model,
                        map_cell=created_city.map_cell).exists():
                    logger.info("Skipping %s, data already imported", model.name)
                else:
                    logger.info("Importing %s", model)
                    import_data(
                        domain=options['domain'],
                        token=options['token'],
                        remote_city_id=city['id'],
                        local_map_cell=created_city.map_cell,
                        scenario=scenario,
                        model=model)

                imported_grid_cells[model.name].append(coordinates)
