import logging

from django.core.management.base import BaseCommand
from django.core.exceptions import ObjectDoesNotExist

from climate_data.management.commands.import_from_other_instance import get_cities, make_request
from climate_data.models import City, HistoricAverageClimateData

import requests

from time import time, sleep

logger = logging.getLogger('climate_data')

CITY_URL = 'https://{domain}/api/city/?format=json'
INDICATOR_URL = 'https://{domain}/api/climate-data/{city}/historical/indicator/{indicator}/?years=1961:1990&units={units}&format=json'  # NOQA

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


def get_historic_data(domain, token, city_id, indicator):
    """
    Gets the historic data for a city from a climate-change-api instance
    """
    url = INDICATOR_URL.format(domain=domain,
                               indicator=indicator['name'],
                               city=city_id,
                               units=indicator['units'])
    return make_request(url, token)


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

            # map of each MM-DD to indicator to aggregated reading for this city
            city_data = {}
            for indicator in INDICATORS:
                data = get_historic_data(options['domain'], options['token'], city['id'], indicator)
                data = data['data']

                # mapping of list of daily values for each year, keyed by date as MM-DD
                dailies = {}
                for year in data.keys():
                    for date in data[year].keys():
                        # strip off leading year from date string of form YYYY-MM-DD
                        month_day = date[5:]
                        # append reading for this year to readings for this date from all years
                        day_readings = dailies.get(month_day, [])
                        day_readings.append(data[year][date])
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
