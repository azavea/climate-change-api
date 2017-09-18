Climate Data
------------

The Climate Data endpoint allows interaction with annual sets of raw projected temperature and precipitation data for any one city and scenario.

.. note:: Requests to this endpoint are `rate-limited`_.

Climate data
____________

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

.. note:: The general format of the response data are objects where the keys are date strings in YYYY-MM-DD format, and the value is an array that always contains 366 values. The value at a given index in the array corresponds to the value for that day of the year. Nulls are days with no data. A null in the 366th position indicates a non-leap year. For simplicity, the data below has been truncated.

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
