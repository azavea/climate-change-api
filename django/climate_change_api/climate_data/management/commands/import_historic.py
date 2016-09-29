import logging

from urllib import urlencode
import numpy as np

from django.core.management.base import BaseCommand

from climate_data.management.commands.import_from_other_instance import get_cities, make_request
from climate_data.models import City, HistoricAverageClimateData, ClimateDataBaseline, ClimateModel

logger = logging.getLogger('climate_data')

CITY_URL = 'https://{domain}/api/city/?format=json'
INDICATOR_URL = 'https://{domain}/api/climate-data/{city}/historical/indicator/{indicator}/?years=1961:1990&units={units}&format=json'  # NOQA
RAWDATA_URL = 'https://{domain}/api/climate-data/{city}/historical/'

INDICATORS = [
    {
        'name': 'daily_high_temperature',
        'units': 'K'
    },
    {
        'name': 'daily_low_temperature',
        'units': 'K'
    },
    {
        'name': 'daily_precipitation',
        'units': 'kg*m^2/s'
    }
]
MODELS = ClimateModel.objects.all()


def get_historic_data(domain, token, city_id, indicator):
    """
    Gets the historic data for a city from a climate-change-api instance
    """
    url = INDICATOR_URL.format(domain=domain,
                               indicator=indicator['name'],
                               city=city_id,
                               units=indicator['units'])
    return make_request(url, token)


def get_historic_raw_data(domain, token, city_id, model=None, variable=None):
    """
    Gets the historic data for a city from a climate-change-api instance
    """
    url = RAWDATA_URL.format(domain=domain,
                             city=city_id)
    params = {}
    if model:
        params['models'] = model
    if variable:
        params['variables'] = variable
    if params:
        url = '{}?{}'.format(url, urlencode(params))

    return make_request(url, token)


def get_precipitation_baseline(domain, token, city, model):
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
        logger.info('Deleting any existing aggregated historic data...')
        HistoricAverageClimateData.objects.all().delete()
        logger.info('Fetching available cities...')
        for city in get_cities(options['domain'], options['token']):
            logger.info('Importing historic data for city %s, %s',
                        city['properties']['name'],
                        city['properties']['admin'])

            records = []
            # find city in local database matching remote
            local_city = City.objects.get(name=city['properties']['name'],
                                          admin=city['properties']['admin'])
            if not local_city:
                logger.warn('Remote city %s, %s does not exist locally; skipping',
                            city['properties']['name'],
                            city['properties']['admin'])
                continue

            record_precipitation_baselines(options['domain'], options['token'], local_city, city['id'])

            # map of each MM-DD to indicator to aggregated reading for this city
            city_data = {}
            for indicator in INDICATORS:
                data = get_historic_data(options['domain'], options['token'], city['id'], indicator)
                data = data['data']

                # mapping of list of daily values for each year, keyed by date as MM-DD
                dailies = {}
                for date, values in data.iteritems():
                    # strip off leading year from date string of form YYYY-MM-DD
                    month_day = date[5:]
                    # append reading for this year to readings for this date from all years
                    day_readings = dailies.get(month_day, [])
                    day_readings.append(values['avg'])
                    dailies[month_day] = day_readings

                # set value for each day to the avearge of all its readings
                for day in dailies.keys():
                    readings = dailies[day]
                    city_data_day = city_data.get(day, {})
                    city_data_day[indicator['name']] = sum(readings) / float(len(readings))
                    city_data[day] = city_data_day

            for day in city_data.keys():
                tasmin = city_data[day].get('daily_low_temperature')
                tasmax = city_data[day].get('daily_high_temperature')
                pr = city_data[day].get('daily_precipitation')
                records.append(HistoricAverageClimateData(city=local_city,
                                                          month_day=day,
                                                          tasmin=tasmin,
                                                          pr=pr,
                                                          tasmax=tasmax))

            logger.info('Creating historic aggregated data records for city')
            HistoricAverageClimateData.objects.bulk_create(records)
