City
----

These endpoints allow users to list, view details of, search and retrieve the boundaries for the locations for which we have climate projections.

A City object is a point feature of the center-most geographic coordinate of an administrative boundary. Each City is associated to a map_cell, a 25 km^2 slice of the Earth's surface. The API breaks up global climate projections by map_cell. Nearby cities, meaning being within the same map_cell, can be expected to experience the same climate.

At this time, only US cities and their climate projection data are available.


.. note:: Paginated city endpoints are |GeoJson|.

.. |GeoJson| raw:: html

   <a href="https://github.com/djangonauts/django-rest-framework-gis#pagination" target="_blank">GeoJson paginated</a>


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
                    "datasets": ["NEX-GDDP", "LOCA"],
                    "proximity": {
                        "ocean": true
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
                    "datasets": ["NEX-GDDP", "LOCA"],
                    "proximity": {
                        "coastal": false
                    }
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
            "datasets": ["NEX-GDDP", "LOCA"],
            "proximity": {
                "ocean": false
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

Get city map cells
__________________

These endpoints expose the underlying grid point used for each city and dataset combination. A grid point maps to a grid cell from the source NetCDF dataset.

Retrieve all available map cells for a given city.

.. openapi:: /openapi/climate_api.yml
    :paths:
        /api/city/{pk}/map-cell/

Example usage
`````````````

.. code-block:: http

    GET /api/city/2/map-cell/ HTTP/1.1
    Host: example.org
    Authorization: Token 46806a08bf54136e9597e879ed3a0876113fdee6

Response:

.. code-block:: http

    HTTP/1.1 200 OK
    Vary: Accept
    Content-Type: application/json

    [
        {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [0,0]
            },
            "properties": {
                "dataset": "NEX-GDDP"
            }
        }, {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [1,1]
            },
            "properties": {
                "dataset": "LOCA"
            }
        }
    ]

Retrieve the map cell for a particular city and dataset combination.

.. openapi:: /openapi/climate_api.yml
    :paths:
        /api/city/{pk}/map-cell/{dataset}/

Example usage
`````````````

.. code-block:: http

    GET /api/city/2/map-cell/LOCA/ HTTP/1.1
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
            "type": "Point",
            "coordinates": [1,1]
        },
        "properties": {
            "dataset": "LOCA"
        }
    }
