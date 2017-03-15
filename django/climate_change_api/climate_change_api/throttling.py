from django.core.cache import caches

from rest_framework.throttling import UserRateThrottle


class UserCustomRateThrottle(UserRateThrottle):
    """ Allow setting custom per-user throttle rates defined in a CharField on your custom Django
        user model

    `model_rate_field`: Specify a custom per-user throttle rate field. Required to override
    the default rate."""

    def allow_request(self, request, view):
        if request.user is not None:
            user_rate = getattr(request.user, self.model_rate_field, self.rate)
            if self.rate != user_rate:
                self.rate = user_rate
                self.num_requests, self.duration = self.parse_rate(self.rate)

        return super(UserCustomRateThrottle, self).allow_request(request, view)


class ClimateDataRateThrottle(UserCustomRateThrottle):
    """ Override to always use the throttling specific cache backend """
    cache = caches['api_throttling']


class ClimateDataBurstRateThrottle(ClimateDataRateThrottle):
    """ Set a relatively low 'burst' rate limit, data queries are relatively expensive """
    scope = 'burst'
    model_rate_field = 'burst_rate'


class ClimateDataSustainedRateThrottle(ClimateDataRateThrottle):
    """ Set a relatively high max daily rate throttle

    Not too concerned about users pulling data slowly over long time periods

    """
    scope = 'sustained'
    model_rate_field = 'sustained_rate'
