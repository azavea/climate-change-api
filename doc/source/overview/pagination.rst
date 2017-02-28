The handful of endpoints with potentially large result sets are paginated.

The API defaults to `limit offset pagination`_ from the Django Rest Framework. Limit pagination has query parameters:

    ``page``: page number of paginated results

    ``page_size``: number of results per page

    ``limit``: a maximum number of features to return

    ``offset``: the starting position in the entire ordered set


The API sets a default ``page_size``, but all pagination parameters may be specified as HTTP query string parameters.

API responses divide up objects returned from the API into pages with maximum length ``page_size`` and nest them in pagination objects:

.. code-block:: json

    {
        "count": 1020,
        "next": "https://api.example.org/accounts/?page=5",
        "previous": "https://api.example.org/accounts/?page=3",
        "results": [ ... ]
    }

Access other pages of data by adjusting the ``page`` number in the links specified in ``next`` or ``previous``.

Some endpoints have other pagination styles. Generally comparable to the above, any differences will be specified where they occur.


.. _`limit offset pagination`: http://www.django-rest-framework.org/api-guide/pagination/#limitoffsetpagination
