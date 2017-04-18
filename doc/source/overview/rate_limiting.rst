
In order to ensure fair access to all users of the Climate API, some endpoints are protected by rate limiting.

If an endpoint is rate limited, the rate limits will be described on that endpoint's API Reference page.

When the rate limit is exceeded, endpoints will return HTTP 429 Too Many Requests along with a descriptive message indicating when the endpoint will be available again:

.. code-block:: json

    {
        "detail": "Request was throttled. Expected available in 18.0 seconds."
    }

In addition, the HTTP header ``Retry-After`` will be set with an integer value in seconds that indicates how long to wait before retrying. For example: ``Retry-After: 43`` indicates that the client should retry the same request after waiting at least 43 seconds.

If you have a use case that requires a call volume that exceeds the default rate limits, feel free to `contact us`_.

.. _`contact us`: climate@azavea.com
