
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

    GET /api/climate-data/1/RCP85/
    Host: example.org

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
                    281.310546875
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
