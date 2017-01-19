from django.core.cache import caches

from rest_framework.throttling import UserRateThrottle


class ClimateDataRateThrottle(UserRateThrottle):
    """ Override to always use the throttling specific cache backend """
    cache = caches['api_throttling']


class ClimateDataBurstRateThrottle(ClimateDataRateThrottle):
    """ Set a relatively low 'burst' rate limit, data queries are relatively expensive """
    rate = '20/min'
    scope = 'burst'


class ClimateDataSustainedRateThrottle(ClimateDataRateThrottle):
    """ Set a relatively high max daily rate throttle

    Not too concerned about users pulling data slowly over long time periods

    """
    rate = '5000/day'
    scope = 'sustained'
