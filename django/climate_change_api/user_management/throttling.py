from django.core.cache import caches

from rest_framework.throttling import AnonRateThrottle


class ObtainAuthTokenThrottle(AnonRateThrottle):
    """ Custom throttling rate for public obtain auth token endpoint """
    cache = caches['api_throttling']
    rate = '5/min'
