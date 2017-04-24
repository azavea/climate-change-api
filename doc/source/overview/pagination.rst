The handful of endpoints with potentially large result sets are paginated.

The API defaults to |limit| from the Django Rest Framework. Limit pagination has query parameters:

    ``limit``: a maximum number of features to return. Defaults to 20.

    ``offset``: the starting position of the query in relation to the complete set of unpaginated items


Each request to the API returns a pagination object with query results of maximum quantity ``limit`` offset in the database by ``offset`` items:

.. code-block:: json

    {
        "count": 1020,
        "next": "https://api.example.org/accounts/?limit=100&offset=400",
        "previous": "https://api.example.org/accounts/?limit=100&offset=200",
        "results": []
    }

Access other pages of data by adjusting the parameters specified in the ``next`` or ``previous`` links.

Some endpoints have other pagination styles than |limit|. Generally comparable to the above, any differences will be specified where they occur.


.. |limit| raw:: html

    <a href="http://www.django-rest-framework.org/api-guide/pagination/#limitoffsetpagination" target="_blank">limit offset pagination</a>
