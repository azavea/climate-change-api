import time

from django.conf import settings

from statsd.defaults.django import statsd


class ClimateRequestLoggingMiddleware(object):
    """Middleware class to submit request/response tracking to StatsD.

    This middleware is configured specifically for metrics sent to Librato using
    their "tags" feature.

    """

    statsd_client = statsd

    def process_view(self, request, view_func, view_args, view_kwargs):
        """Attach metadata and timing data about the view to the request object."""
        view = view_func
        # Check to determine if this is a function
        if not hasattr(view_func, '__call__'):
            view = view.__class__

        try:
            request._module_name = view.__module__.partition('.')[0]
            request._view_name = view.__name__
            request._start_time = time.time()
            request._metric = 'views'

            request._tags = {
                'environment': settings.ENVIRONMENT.lower(),
                'module': request._module_name,
                'view': request._view_name,
                'method': request.method,
            }
        except AttributeError:
            pass

    def process_response(self, request, response):
        """Send timing and count info to statsd on successful responses."""
        if hasattr(request, '_metric'):
            self._add_metric_tags(request)
            self._record_view_count(request)
            self._record_view_status_code(request, response.status_code)
            if hasattr(response, 'content'):
                self._record_view_size(request, len(response.content))
            self._record_time(request)

        return response

    def process_exception(self, request, exception):
        """Send timing and count info to statsd on unsuccessful responses."""
        if hasattr(request, '_metric'):
            self._add_metric_tags(request)
            self._record_view_count(request)
            self._record_view_status_code(request, 500)
            self._record_time(request)

    def _add_metric_tags(self, request):
        if request.user.is_authenticated:
            request._tags['user'] = request.user.id
            request._tags['organization'] = request.user.userprofile.organization.lower()

    def _construct_librato_metric(self, metric, tags=None):
        if tags is not None:
            tags = ['{}={}'.format(k, v) for k, v in tags.items()]
            tags = ','.join(tags)
            metric = '{}#{}'.format(metric, tags)
        return metric

    def _record_time(self, request):
        """Extract metadata and timing data attached to request object and submit to statsd.

        Args:
            request (HttpRequest): Request being timed
        """
        if hasattr(request, '_metric'):
            metric = '{}.response.time'.format(request._metric)
            metric = self._construct_librato_metric(metric, tags=request._tags)
            delta = int((time.time() - request._start_time) * 1000)
            self.statsd_client.timing(metric, delta)

    def _record_view_count(self, request):
        """Record a view count metric.

        Assumes the request metric and tags properties already have all relevant items set

        """
        if hasattr(request, '_metric'):
            metric = '{}.count'.format(request._metric)
            metric = self._construct_librato_metric(metric, tags=request._tags)
            self.statsd_client.incr(metric)

    def _record_view_status_code(self, request, status_code):
        """Record a view HTTP status code metric.

        Assumes the request metric and tags properties already have all relevant items set

        """
        if hasattr(request, '_metric'):
            metric = '{}.http.{}'.format(request._metric, status_code)
            metric = self._construct_librato_metric(metric, tags=request._tags)
            self.statsd_client.incr(metric)

    def _record_view_size(self, request, response_size):
        """Record view size as a timer.

        Assumes the request metric and tags properties already have all relevant items set

        """
        if hasattr(request, '_metric'):
            metric = '{}.response.size'.format(request._metric)
            metric = self._construct_librato_metric(metric, tags=request._tags)
            self.statsd_client.timing(metric, response_size)
