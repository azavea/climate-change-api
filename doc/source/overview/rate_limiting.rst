
In order to ensure fair access to all users of the Climate API, certain resources are protected by rate limiting.

If a resource is rate limited, the rate limits will be described on that resource's API Reference page.

All resources that are rate limited will return HTTP 429 Too Many Requests along with a descriptive message indicating when the resource will be available again:

.. code-block:: json

    {
        "detail": "Request was throttled. Expected available in 18.0 seconds."
    }


If you have a use case that requires a call volume that exceeds the default rate limits, feel free to `contact us`_.

.. _`contact us`: support@futurefeelslike.com
