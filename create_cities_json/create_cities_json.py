#!/usr/bin/env python3

import logging
import argparse
import json
import csv


FIELD_NAMES = (
    'geonameid',
    'name',
    'asciiname',
    'alternatenames',
    'latitude',
    'longitude',
    'feature class',
    'feature code',
    'country code',
    'cc2',
    'admin1 code',
    'admin2 code',
    'admin3 code',
    'admin4 code',
    'population',
    'elevation',
    'dem',
    'timezone',
    'modification date'
)

logger = logging.getLogger(__name__)


def load_geonames(filename):
    with open(filename, 'r') as f:
        csvreader = csv.DictReader(f, fieldnames=FIELD_NAMES, delimiter='\t',
                                   quoting=csv.QUOTE_NONE)
        return [line for line in csvreader if line['feature class'] in ('A', 'P', 'L')]


def load_import_list(filename):
    with open(filename, 'r') as f:
        csvreader = csv.DictReader(f, fieldnames=('city', 'state'))
        return [line for line in csvreader]


def pick_geoname(geonames, city, state):
    city = city.upper()
    for geoname in geonames:
        if (geoname['country code'] == 'US' and
                geoname['admin1 code'] == state and
                geoname['name'].upper() == city):
            return geoname
    for geoname in geonames:
        if (geoname['country code'] == 'US' and
                geoname['admin1 code'] == state and
                city in geoname['alternatenames'].upper().split(',')):
            logger.info('%s found in alternate names %s %s', city, geoname['name'],
                        geoname['admin1 code'])
            return geoname
    return None


def geoname_to_geojson(geoname):
    return {
        'type': 'Feature',
        'geometry': {
            'type': 'Point',
            'coordinates': [float(geoname['longitude']), float(geoname['latitude'])]
        },
        'properties': {
            'name': geoname['name'],
            'admin1': geoname['admin1 code'],
            'population': geoname['population']
        }
    }


def main():
    parser = argparse.ArgumentParser(
        description='Generate a GeoJSON suitable for import into the climate-change-api '
        'from geonames\' US.txt and an import list CSV formatted as CITY,STATE (with the two '
        'letter state abbreviation)')
    parser.add_argument('GEONAMES', type=str)
    parser.add_argument('IMPORTLIST', type=str)
    args = parser.parse_args()
    import_list = load_import_list(args.IMPORTLIST)
    geonames = load_geonames(args.GEONAMES)
    features = {}
    for city in import_list:
        if not city['city'] or not city['state']:
            continue
        geoname = pick_geoname(geonames, city['city'].strip(), city['state'].strip())
        if geoname:
            features[geoname['name'], geoname['admin1 code']] = geoname_to_geojson(geoname)
        else:
            logger.warn('Could not find %s %s', city['city'], city['state'])
    geojson = {
        'type': 'FeatureCollection',
        'features': list(features.values())
    }
    with open('cities.geojson', 'w') as output:
        json.dump(geojson, output, indent=2)


if __name__ == '__main__':
    main()
