import logging

from django.core.management.base import BaseCommand

from django.contrib.gis.geos import Point

from climate_data.models import (
    City, Scenario, ClimateModel, ClimateDataSource, ClimateDataCell, ClimateData
)

import requests

from time import time

logger = logging.getLogger('climate_data')

MODEL_LIST_URL = 'https://{domain}/api/climate-model/'
CITY_LIST_URL = 'https://{domain}/api/city/'
CLIMATE_DATA_URL = 'https://{domain}/api/climate-data/{city_id}/{rcp}/?models={model}'


def get_models(domain, token):
    """
    Returns a list of available models from an instance of climate-change-api
    """
    url = MODEL_LIST_URL.format(domain=domain)
    logger.info('Fetching %s', url)
    res = requests.get(url, headers={'Authorization': 'Token {}'.format(token)})
    return map(lambda d: d['name'], res.json())


def get_cities(domain, token):
    """
    Returns an iterable of city dicts from an instance of climate-change-api
    """
    url = CITY_LIST_URL.format(domain=domain)
    while url:
        logger.info('Fetching %s', url)
        res = requests.get(url, headers={'Authorization': 'Token {}'.format(token)})
        data = res.json()
        for feature in data['features']:
            yield feature
        url = data['next']


def get_data(domain, token, city_id, rcp, model):
    """
    Gets all the data for a city for a given rcp and model from a climate-change-api instance
    """
    url = CLIMATE_DATA_URL.format(domain=domain, city_id=city_id, rcp=rcp, model=model)
    logger.info('Fetching %s', url)
    start_time = time()
    res = requests.get(url, headers={'Authorization': 'Token {}'.format(token)})
    logger.info('Fetched in %f s', time() - start_time)
    return res.json()


def create_models(models):
    """
    Create the ClimateModels given
    """
    ClimateModel.objects.bulk_create([
        ClimateModel(name=name)
        for name in models
    ])


def create_city(citydata):
    """
    Create a city and if not already created, it's grid cell from the city dict
    downloaded from another instance
    """
    data_cell = ClimateDataCell.objects.get_or_create(
        id=citydata['properties']['map_cell'],
        defaults={
            'lat': citydata['geometry']['coordinates'][1],
            'lon': citydata['geometry']['coordinates'][0]
        }
    )[0]
    City(
        id=citydata['id'],
        geom=Point(*citydata['geometry']['coordinates']),
        _geog=Point(*citydata['geometry']['coordinates']),
        map_cell=data_cell,
        name=citydata['properties']['name'],
        admin=citydata['properties']['admin']
    ).save()


def import_data(data):
    """
    Import the the output of get_data into the database
    """
    start_time = time()
    map_cell = data['city']['properties']['map_cell']
    assert len(data['climate_models']) == 1
    model = ClimateModel.objects.get(name=data['climate_models'][0])
    scenario = Scenario.objects.get(name=data['scenario'])
    for year, yeardata in data['data'].iteritems():
        data_source = ClimateDataSource.objects.get_or_create(model=model,
                                                              scenario=scenario,
                                                              year=int(year))[0]
        ClimateData.objects.bulk_create([
            ClimateData(map_cell_id=map_cell,
                        data_source=data_source,
                        day_of_year=day,
                        tasmin=tasmin,
                        tasmax=tasmax,
                        pr=pr)
            for day, (tasmin, tasmax, pr) in enumerate(zip(yeardata['tasmin'],
                                                           yeardata['tasmax'],
                                                           yeardata['pr']), start=1)])
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
        models = get_models(options['domain'], options['token'])
        if len(models) > options['num_models']:
            models = models[:options['num_models']]
        create_models(models)
        imported_grid_cells = []
        for i, city in enumerate(get_cities(options['domain'], options['token'])):
            if i > options['num_cities']:
                break
            create_city(city)
            logger.info('Importing city %s, %s',
                        city['properties']['name'],
                        city['properties']['admin'])
            if city['properties']['map_cell'] not in imported_grid_cells:
                for model in models:
                    import_data(get_data(options['domain'], options['token'],
                                         city['id'],
                                         options['rcp'],
                                         model))
                imported_grid_cells.append(city['properties']['map_cell'])
