import time

from statsd.defaults.django import statsd


class ClimateRequestLoggingMiddleware(object):
    """Middleware class to submit request/response timing data to StatsD.

    Much of this class is based on the ``GraphiteRequestTimingMiddleware``
    of ``django-statsd``. Most of the changes were to reduce external
    dependencies and better tailor the solution to our use case.
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
            request._tag = 'views.{module}.{name}.{method}'.format(module=request._module_name,
                                                                   name=request._view_name,
                                                                   method=request.method)
        except AttributeError:
            pass

    def process_response(self, request, response):
        """Send timing and count info to statsd on successful responses."""
        if hasattr(request, '_tag'):
            # Send view/user count metric
            tag = '{}.{}'.format(request._tag, response.status_code)
            if request.user.is_authenticated:
                tag += '.{}'.format(request.user.encode_email().decode('ascii'))

            self.statsd_client.incr(tag)
            # Send view timing metric
            self._record_time(request._start_time, tag)
            # Send view size metric
            if hasattr(response, 'content'):
                statsd.timing('{}.size'.format(tag), len(response.content))

        return response

    def process_exception(self, request, exception):
        """Send timing and count info to statsd on unsuccessful responses."""
        if hasattr(request, '_tag'):
            # Send view/user count metric
            tag = '{}.{}'.format(request._tag, '500')
            if request.user.is_authenticated:
                tag += '.{}'.format(request.user.encode_email().decode('ascii'))

            self.statsd_client.incr(tag)
            # Send view timing metric
            self._record_time(request._start_time, tag)

    def _record_time(self, start_time, tag):
        """Extract metadata and timing data attached to response object and submit to statsd.

        Args:
            start_time (time.time): Start time of the request being processed
            tag (str): Tag to send to statsd
        """
        delta = int((time.time() - start_time) * 1000)
        statsd.timing(tag, delta)
