Climate Data
------------

The Climate Data endpoints allow interaction with annual sets of raw projected temperature and precipitation data for any one location and scenario.

.. note:: Requests to this endpoint are `rate-limited`_.

.. note:: The general format of the response data are objects where the keys are date strings in YYYY-MM-DD format, and the value is an array that always contains 366 values. The value at a given index in the array corresponds to the value for that day of the year. Nulls are days with no data. A null in the 366th position indicates a non-leap year. For simplicity, the data below has been truncated.


Climate data by City
_____________________

.. openapi:: /openapi/climate_api.yml
    :paths:
        /api/climate-data/{city}/{scenario}/

Example usage
`````````````

.. code-block:: http

    GET /api/climate-data/1/RCP85/ HTTP/1.1
    Host: example.org
    Authorization: Token 46806a08bf54136e9597e879ed3a0876113fdee6

Response:

.. code-block:: http

    HTTP/1.1 200 OK
    Vary: Accept
    Content-Type: application/json

    {
        "city": {
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
                "datasets": [
                    "NEX-GDDP"
                ],
                "proximity": {
                    "ocean": true
                },
                "name": "New York City",
                "admin": "NY",
                "population": 8175133
            }
        },
        "dataset": "NEX-GDDP",
        "scenario": "RCP85",
        "climate_models": [
            "ACCESS1-0",
            "BNU-ESM"
        ],
        "variables": [
            "tasmax",
            "pr",
            "tasmin"
        ],
        "data": {
            "2050": {
                "tasmax": [
                    279.064025878906,
                    281.310546875,
                ],
                "tasmin": [
                    271.326614379883,
                    273.004791259766
                ],
                "pr": [
                    0.0000122705498775133,
                    0
                ]
            }
        }
    }


Climate data by Lat + Lon
_________________________

.. openapi:: /openapi/climate_api.yml
    :paths:
        /api/climate-data/{lat}/{lon}/{scenario}/

Example usage
`````````````

.. code-block:: http

    GET /api/climate-data/44.525/-110.838/RCP85/ HTTP/1.1
    Host: example.org
    Authorization: Token 46806a08bf54136e9597e879ed3a0876113fdee6

Response:

.. code-block:: http

    HTTP/1.1 200 OK
    Vary: Accept
    Content-Type: application/json

    {
        "feature": {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [249.75, 44.5]
            },
            "properties": {
                "proximity": {
                    "ocean": false
                }
            }
        },
        "dataset": "NEX-GDDP",
        "scenario": "RCP85",
        "climate_models": [
            "ACCESS1-0",
            "BNU-ESM"
        ],
        "variables": [
            "tasmax",
            "pr",
            "tasmin"
        ],
        "data": {
            "2050": {
                "tasmax": [
                    279.064025878906,
                    281.310546875,
                ],
                "tasmin": [
                    271.326614379883,
                    273.004791259766
                ],
                "pr": [
                    0.0000122705498775133,
                    0
                ]
            }
        }
    }


.. _`rate-limited`: overview.html#rate-limiting
