from collections import OrderedDict

import requests
from retry import retry

from django.contrib.gis.geos import MultiPolygon, Polygon

from .exceptions import GeoBoundaryError


class CensusBoundaryError(GeoBoundaryError):
    pass


@retry((requests.exceptions.ConnectionError,), tries=3, delay=1, backoff=2)
def geocoder_api_request(return_type, search_type, params=None):
    """ Make a request to the Census Geocoder API

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


@retry((requests.exceptions.ConnectionError,), tries=3, delay=1, backoff=2)
def map_server_request(layer_id, params=None):
    """ Make a request to the Census Map Server

    Returns the map server query response directly.
    Forces use of the f=pjson query param

    :param layer_id: int - One of the layer ids at https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/tigerWMS_Current/MapServer
    :param params: dict - Query params to pass to API request.

    """

    if params is None:
        params = {}

    CENSUS_MAP_SERVER_URL_TEMPLATE = ('https://tigerweb.geo.census.gov/arcgis/rest/services' +
                                      '/TIGERweb/tigerWMS_Current/MapServer/{layer_id}/query')
    url = CENSUS_MAP_SERVER_URL_TEMPLATE.format(layer_id=layer_id)

    params['f'] = 'pjson'
    response = requests.get(url, params=params)
    return response.json()


def boundary_from_point(point, srid=4326):
    """ Return an appropriate boundary from the Census API for a given Point

    This method provides a relatively generic interface that boundary_from_point methods
    from other services could also implement. It also remains flexible in case we want to
    load boundaries via a method other than API calls.

    raises GeoBoundaryError or a subclass of it if no boundary can be found.

    :param point: django.contrib.gis.geos.Point
    :param srid: int - Desired SRID of the MultiPolygon boundary. Default: 4326.
    :return (boundary: MultiPolygon, boundary_type: str). The associated boundary and its type.

    """
    CENSUS_LAYERS = OrderedDict([
        ('Incorporated Places', 28),
        ('Census Designated Places', 30),
        ('Counties', 86),
    ])

    params = {
        'benchmark': 'Public_AR_Current',
        'vintage': 'Current_Current',
        'x': point.x,
        'y': point.y,
        'layers': ','.join(CENSUS_LAYERS.keys())
    }
    results = geocoder_api_request('geographies', 'coordinates', params=params)

    for boundary_type, layer_id in CENSUS_LAYERS.iteritems():
        boundaries = results['geographies'][boundary_type]
        if len(boundaries) > 0:
            boundary = boundaries[0]
            params = {
                'where': 'OID={}'.format(boundary['OID']),
                'returnGeometry': 'true',
                'outSr': srid,
                'f': 'pjson',
            }
            results = map_server_request(layer_id, params=params)
            features = results['features']
            geometry_type = results['geometryType']
            # ArcGIS MapServer doesn't have a multipolygon type so only check for Polygon
            if len(features) > 0 and geometry_type == 'esriGeometryPolygon':
                feature = features[0]
                rings = feature['geometry']['rings']
                geom = Polygon(*rings, srid=srid)
                return (MultiPolygon(geom), boundary_type,)

    # Default to raising instance of GeoBoundaryError if no boundary
    # This shouldn't ever happen since Counties have 100% area coverage
    raise CensusBoundaryError("Failed to create census boundary for Point: {}".format(point))
