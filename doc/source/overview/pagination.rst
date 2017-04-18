The endpoints with potentially large result sets are paginated.

The API defaults to `limit offset pagination`_ from the Django Rest Framework. Limit pagination has query parameters:

    ``limit``: a maximum number of features to return. Defaults to 20.

    ``offset``: the starting position of the query in relation to the complete set of unpaginated items


Each request to the API returns a pagination object with query results of maximum ``limit`` items offset by ``offset`` items:

.. code-block:: json

    {
        "count": 1020,
        "next": "https://api.example.org/accounts/?limit=100&offset=400",
        "previous": "https://api.example.org/accounts/?limit=100&offset=200",
        "results": []
    }

Access other pages of data by adjusting the parameters specified in the ``next`` or ``previous`` links.

Some endpoints have pagination styles other than `limit offset pagination`_. Differences will be specified where they occur.


.. _`limit offset pagination`: http://www.django-rest-framework.org/api-guide/pagination/#limitoffsetpagination
