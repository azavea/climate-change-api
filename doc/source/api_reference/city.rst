
These endpoints allow users to list, view details of, search and retrieve the boundaries for the locations for which we have climate projections.

A City object is a point feature of the center-most geographic coordinate of an administrative boundary. Each City is associated to a map_cell, a 25 km^2 slice of the Earth's surface. The API breaks up global climate projections by map_cell. Nearby cities, meaning being within the same map_cell, can be expected to experience the same climate.

At this time, only US cities and their climate projection data are available.

The city endpoints with potentially large result sets are `limit paginated`_ according to Django Rest Framework. As a result, responses take the pagination object structure, where returned city objects are split into pages and nested in ``features``. Access other pages by the links specified in the ``next`` and ``previous`` fields::

    {
        "count": 1020,
        "next": "https://api.example.org/accounts/?page=5",
        "previous": "https://api.example.org/accounts/?page=3",
        "features": [ ... ]
    }

In limit pagination, a cap may specify maximum number of features to return. The API sets a default ``page_size`` and ``limit``, but these and other optional pagination parameters may be specified as HTTP query string parameters.


List Cities
___________

.. openapi:: /openapi/climate_api.yml
    :paths:
        /api/city/

Example usage
`````````````

.. code-block:: http

    GET /api/city/ HTTP/1.1
    Host: example.org
    Authorization: Token 46806a08bf54136e9597e879ed3a0876113fdee6

Response:

.. code-block:: http

    HTTP/1.1 200 OK
    Vary: Accept
    Content-Type: application/json

    {
        "type": "FeatureCollection",
        "count": 1,
        "next": "http://example.org/api/city/?page=2",
        "previous": null,
        "features": [
            {
                "id": 1,
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [
                        -74.00597,
                        40.71427
                    ]
                },
                "properties": {
                    "map_cell": {
                        "type": "Point",
                        "coordinates": [
                                285.875,
                                40.625
                        ]
                    },
                    "name": "New York City",
                    "admin": "NY",
                    "population": 8175133
                }
            }
        ]
    }

Nearest city or cities
______________________
.. openapi:: /openapi/climate_api.yml
    :paths:
        /api/city/nearest/

Example usage
`````````````

.. code-block:: http

    GET /api/city/nearest/?lat=40&lon=285 HTTP/1.1
    Host: example.org
    Authorization: Token 46806a08bf54136e9597e879ed3a0876113fdee6

Response:

.. code-block:: http

    HTTP/1.1 200 OK
    Vary: Accept
    Content-Type: application/json

    {
        "type": "FeatureCollection",
        "count": 1,
        "next": null,
        "previous": null,
        "features": [
            {
                "id": 2,
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [
                        -75.16379,
                        39.95233
                    ]
                },
                "properties": {
                    "map_cell": {
                        "type": "Point",
                        "coordinates": [
                            284.875,
                            39.875
                        ]
                    },
                    "name": "Philadelphia",
                    "admin": "PA",
                    "population": 1526006
                }
            }
        ]
    }

Request city
____________
.. openapi:: /openapi/climate_api.yml
    :paths:
        /api/city/{pk}/

Example usage
`````````````

.. code-block:: http

    GET /api/city/2/ HTTP/1.1
    Host: example.org
    Authorization: Token 46806a08bf54136e9597e879ed3a0876113fdee6

Response:

.. code-block:: http

    HTTP/1.1 200 OK
    Vary: Accept
    Content-Type: application/json

    {
        "id": 2,
        "type": "Feature",
        "geometry": {
            "type": "Point",
            "coordinates": [
                -75.16379,
                39.95233
            ]
        },
        "properties": {
            "map_cell": {
                "type": "Point",
                "coordinates": [
                    284.875,
                    39.875
                ]
            },
            "name": "Philadelphia",
            "admin": "PA",
            "population": 1526006
        }
    }

Get city boundary
_________________
.. openapi:: /openapi/climate_api.yml
    :paths:
        /api/city/{pk}/boundary/

Example usage
`````````````

.. code-block:: http

    GET /api/city/2/boundary/ HTTP/1.1
    Host: example.org
    Authorization: Token 46806a08bf54136e9597e879ed3a0876113fdee6

Response:

.. code-block:: http

    HTTP/1.1 200 OK
    Vary: Accept
    Content-Type: application/json

    {
        "type": "Feature",
        "geometry": {
            "type": "MultiPolygon",
            "coordinates": [
                [
                    [
                        [
                            0,
                            0
                        ]
                    ]
                ]
            ]
        }
    }

.. _`limit paginated`: https://github.com/tomchristie/django-rest-framework/blob/master/rest_framework/pagination.py
