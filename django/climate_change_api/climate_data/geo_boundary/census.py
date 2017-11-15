from collections import OrderedDict
import json
import logging

import requests
from retry import retry

from esridump.dumper import EsriDumper

from django.contrib.gis.geos import GEOSGeometry, Polygon, MultiPolygon

from .exceptions import GeoBoundaryError

logger = logging.getLogger(__name__)


CENSUS_MAP_SERVER_URL_TEMPLATE = ('https://tigerweb.geo.census.gov/arcgis/rest/services' +
                                  '/TIGERweb/tigerWMS_Current/MapServer/{layer_id}')

CENSUS_LAYERS = OrderedDict([
    ('Incorporated Places', 28),
    ('Census Designated Places', 30),
    ('Counties', 86),
])


class CensusBoundaryError(GeoBoundaryError):
    pass


@retry((requests.exceptions.ConnectionError,), tries=3, delay=1, backoff=2)
def geocoder_api_request(return_type, search_type, params=None):
    """Make a request to the Census Geocoder API.

    Returns a dict of the 'result' key of the API response, forces use of the format=json param

    Documentation at: https://geocoding.geo.census.gov/geocoder/Geocoding_Services_API.pdf

    :param return_type: str
    :param search_type: str
    :param params: dict - Query params to pass to API request
    """
    VALID_RETURN_TYPES = ('locations', 'geographies',)
    VALID_SEARCH_TYPES = ('onelineaddress', 'address', 'coordinates',)
    URL_PREFIX = 'https://geocoding.geo.census.gov/geocoder'
    if params is None:
        params = {}
    if return_type not in VALID_RETURN_TYPES:
        raise ValueError('return_type must be one of {}'.format(VALID_RETURN_TYPES))
    if search_type not in VALID_SEARCH_TYPES:
        raise ValueError('search_type must be one of {}'.format(VALID_SEARCH_TYPES))

    params['format'] = 'json'

    url = '{}/{}/{}'.format(URL_PREFIX, return_type, search_type)
    response = requests.get(url, params=params)
    data = response.json()
    return data['result']


def boundary_from_point(point, srid=4326):
    """Return an appropriate boundary from the Census API for a given Point.

    This method provides a relatively generic interface that boundary_from_point methods
    from other services could also implement. It also remains flexible in case we want to
    load boundaries via a method other than API calls.

    raises GeoBoundaryError or a subclass of it if no boundary can be found.

    :param point: django.contrib.gis.geos.Point
    :param srid: int - Desired SRID of the MultiPolygon boundary. Default: 4326.
    :return (boundary: MultiPolygon, boundary_type: str). The associated boundary and its type.
    """

    if not point.x and not point.y:
        raise CensusBoundaryError("Cannot get census boundary for missing Point: {}".format(point))

    def geom_from_census_boundary(boundary, layer_id, srid=4326):
        params = {
            'where': 'OID={}'.format(boundary['OID'])
        }
        dumper = EsriDumper(CENSUS_MAP_SERVER_URL_TEMPLATE.format(layer_id=layer_id),
                            extra_query_args=params)

        # return a multipolygon that is the union of the polygons in the returned features
        return_poly = None
        for x in dumper:
            geom = GEOSGeometry(json.dumps(x['geometry']), srid=srid)
            if not return_poly:
                return_poly = geom
            else:
                return_poly = return_poly.union(geom)
        if not return_poly.valid:
            logger.warn('Fixing Census boundary polygon for OID {}'.format(boundary['OID']))
            # buffering to zero can fix some geometry issues, such as ring self-intersections
            return_poly = return_poly.buffer(0)

        # wrap Polygon objects in a MultiPolygon, for consistent return type
        if isinstance(return_poly, Polygon):
            return_poly = MultiPolygon(return_poly)

        if return_poly.valid:
            return return_poly
        else:
            # might occur if attempting to fix by buffering above failed
            logger.exception('Census boundary polygon invalid for OID {}'.format(boundary['OID']))
            return None

    params = {
        'benchmark': 'Public_AR_Current',
        'vintage': 'Current_Current',
        'x': point.x,
        'y': point.y,
        'layers': ','.join(CENSUS_LAYERS.keys())
    }
    results = geocoder_api_request('geographies', 'coordinates', params=params)

    for boundary_type, layer_id in CENSUS_LAYERS.items():
        boundaries = results['geographies'][boundary_type]
        if len(boundaries) > 0:
            try:
                geom = geom_from_census_boundary(boundaries[0], layer_id, srid=srid)
            except KeyError as e:
                geom = None
                logger.info('KeyError in boundary_for_point %s: %s. %s skipped.',
                            point, e, boundary_type)
            if geom:
                return (geom, boundary_type,)
        logger.info('No boundary of type %s at point %s', boundary_type, point)

    # Default to raising instance of GeoBoundaryError if no boundary
    # This shouldn't ever happen since Counties have 100% area coverage
    raise CensusBoundaryError("Failed to create census boundary for Point: {}".format(point))
