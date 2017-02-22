from django.core.cache import caches

from rest_framework.throttling import UserRateThrottle


class ClimateDataRateThrottle(UserRateThrottle):
    """ Override to always use the throttling specific cache backend """
    cache = caches['api_throttling']


class ClimateDataBurstRateThrottle(ClimateDataRateThrottle):
    """ Set a relatively low 'burst' rate limit, data queries are relatively expensive """
    scope = 'burst'

    def allow_request(self, request, view):
        if self.rate != request.user.burst_rate:
            self.rate = request.user.burst_rate
            self.num_requests, self.duration = self.parse_rate(self.rate)

        return super(ClimateDataBurstRateThrottle, self).allow_request(request, view)


class ClimateDataSustainedRateThrottle(ClimateDataRateThrottle):
    """ Set a relatively high max daily rate throttle

    Not too concerned about users pulling data slowly over long time periods

    """
    scope = 'sustained'

    def allow_request(self, request, view):
        if self.rate != request.user.sustained_rate:
            self.rate = request.user.sustained_rate
            self.num_requests, self.duration = self.parse_rate(self.rate)

        return super(ClimateDataSustainedRateThrottle, self).allow_request(request, view)
