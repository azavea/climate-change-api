import logging

from urllib import urlencode
import numpy as np
from itertools import izip

from django.core.management.base import BaseCommand

from climate_data.management.commands.import_from_other_instance import get_cities, make_request
from climate_data.models import City, HistoricAverageClimateData, ClimateDataBaseline, ClimateModel

logger = logging.getLogger('climate_data')

CITY_URL = 'https://{domain}/api/city/?format=json'

RAWDATA_URL = 'https://{domain}/api/climate-data/{city}/historical/'
VARIABLES = ['tasmin', 'tasmax', 'pr']
MODELS = ClimateModel.objects.all()


def get_historic_raw_data(domain, token, city_id, model=None, variable=None):
    """
    Gets the historic data for a city from a climate-change-api instance
    """
    url = RAWDATA_URL.format(domain=domain,
                             city=city_id)
    params = {}
    if model is None:
        params['models'] = model
    if variable is None:
        params['variables'] = variable
    if params:
        url = '{}?{}'.format(url, urlencode(params))

    return make_request(url, token)


def get_precipitation_baseline(domain, token, city, model):
    logger.warn('Getting precipitation baselines for %s',
                    model.name)
    response = get_historic_raw_data(domain, token, city, model.name, 'pr')
    data = response['data']

    # Use a generator to extract the precip data from each year
    precip = (year['pr'] for year in data.values())

    # Flatten the list-of-lists into a single list of straight values
    flat_precip = (v for years_data in precip for v in years_data)

    # Remove any readings with no precipitation that day
    rainfall = (v for v in flat_precip if v > 0)

    # Calculate the 99th percentile of the data
    return np.percentile(list(rainfall), 99)


def record_precipitation_baselines(domain, token, local_city, remote_city_id):
    if ClimateDataBaseline.objects.filter(map_cell=local_city.map_cell).exists():
        return

    # We received a list of data by year, but we want pure numbers
    # Flatten the lists into a single master list

    precip_99ps = (get_precipitation_baseline(domain, token, remote_city_id, model) for model in MODELS)

    baseline = ClimateDataBaseline(
        map_cell=local_city.map_cell,
        precip_99p=np.mean(list(precip_99ps))
    )
    baseline.save()


class Command(BaseCommand):
    help = 'Downloads historic data from a remote instance and imports computed aggregates'

    def add_arguments(self, parser):
        parser.add_argument('domain', type=str, help='domain name of the remote instance')
        parser.add_argument('token', type=str, help='API token for authorization')

    def handle(self, *args, **options):
        logger.info('Fetching available cities...')
        for city in get_cities(options['domain'], options['token']):
            logger.info('Importing historic data for city %s, %s',
                        city['properties']['name'],
                        city['properties']['admin'])

            # find city in local database matching remote
            local_city = City.objects.get(name=city['properties']['name'],
                                          admin=city['properties']['admin'])
            if not local_city:
                logger.warn('Remote city %s, %s does not exist locally; skipping',
                            city['properties']['name'],
                            city['properties']['admin'])
                continue

            if HistoricAverageClimateData.objects.filter(map_cell=local_city.map_cell).exists():
                logger.warn('City %s, %s already imported, skipping',
                            city['properties']['name'],
                            city['properties']['admin'])
                continue

            response = get_historic_raw_data(options['domain'], options['token'], city['id'])
            data = response['data']

            # Convert the list into a list of year/readings sets arranged by variable, like
            # (((y1d1, y1d2, ...), (y2d1, y2d2, ...), ...),  <- tasmin
            #  ((y1d1, y1d2, ...), (y2d1, y2d2, ...), ...),  <- tasmax
            #  ((y1d1, y1d2, ...), (y2d1, y2d2, ...), ...))  <- pr
            variable_data = ((year[var] for year in data.values()) for var in VARIABLES)

            # Join the years together on day, so we have a structure like
            # (((y1d1, y2d1, ...), (y1d2, y2d2, ...), ...),  <- tasmin
            #  ((y1d1, y2d1, ...), (y1d2, y2d2, ...), ...),  <- tasmax
            #  ((y1d1, y2d1, ...), (y1d2, y2d2, ...), ...))  <- pr
            # n.b. izip is the iterative version of zip, allowing lazy evaluation
            day_tuples = (izip(*years) for years in variable_data)

            # Join the days together so we have a tuple per day with yearly
            # readings grouped by variable
            #        tasmin             tasmax                pr
            # (((y1d1, y2d1, ...), (y1d1, y2d1, ...), (y1d1, y2d1, ...)),
            #  ((y1d2, y2d2, ...), (y1d2, y2d2, ...), (y1d2, y2d2, ...)), ...)
            day_variable_tuples = izip(*day_tuples)

            records = (HistoricAverageClimateData(
                    map_cell=local_city.map_cell,
                    day_of_year=day_of_year,
                    # Some models might not have data for a specific day, so we
                    #  need to exclude those values from the average
                    tasmin=np.mean([v for v in tasmin if v is not None]),
                    tasmax=np.mean([v for v in tasmax if v is not None]),
                    pr=np.mean([v for v in pr if v is not None]))
                for (day_of_year, (tasmin, tasmax, pr)) in enumerate(day_variable_tuples))

            logger.info('Creating historic aggregated data records for city')
            HistoricAverageClimateData.objects.bulk_create(records)
