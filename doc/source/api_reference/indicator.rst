
The Indicator endpoints detail all of the derived data "indicators" that are available. The indicators provided by the Climate API are derived quantities generated using the same raw data provided by `Climate Data`_.

If you have ideas for Indicators that aren't provided by the Climate API, but might like to add, please `contact us`_.

Indicator List
______________

.. openapi:: /openapi/climate_api.yml
    :paths:
        /api/indicator/

Example usage
`````````````

.. code-block:: http

    GET /api/indicator/ HTTP/1.1
    Host: example.org
    Authorization: Token 46806a08bf54136e9597e879ed3a0876113fdee6

Response:

.. code-block:: http

    HTTP/1.1 200 OK
    Vary: Accept
    Content-Type: application/json

    {
        "results": [
            {
                "name": "example_temperature_indicator",
                "label": "Example Temperature Indicator",
                "description": "Simplified indicator to demonstrate the response format",
                "valid_aggregations": [
                    "yearly",
                    "monthly"
                ],
                "variables": [
                    "tasmax",
                    "tasmin"
                ],
                "available_units": [
                    "C",
                    "K",
                    "F"
                ],
                "default_units": "F",
                "parameters": [
                    {
                        "name": "example",
                        "description": "Example parameter",
                        "required": false,
                        "default": false
                    }
                ]
            }
        ]
    }


Indicator Data
______________

Returns data for a specified indicator and its unique required and optional query parameters. See `Indicator detail`_ for more information about these parameters.

.. note:: Requests to this endpoint are `rate-limited`_.

.. openapi:: /openapi/climate_api.yml
    :paths:
        /api/climate-data/{city}/{scenario}/indicator/{indicator-name}/

Example usage
`````````````

.. code-block:: http

    GET /api/climate-data/1/RCP85/example_temperature_indicator HTTP/1.1
    Host: example.org
    Authorization: Token 46806a08bf54136e9597e879ed3a0876113fdee6

Response:

.. code-block:: http

    HTTP/1.1 200 OK
    Vary: Accept
    Content-Type: application/json

    {
        "city": {
            "id": 2,
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
        "indicator": {
            "name": "example_temperature_indicator",
            "label": "Example Temperature Indicator",
            "description": "Simplified indicator to demonstrate the response format",
            "valid_aggregations": [
                "yearly",
                "monthly"
            ],
            "variables": [
                "tasmax",
                "tasmin"
            ],
            "available_units": [
                "C",
                "K",
                "F"
            ],
            "default_units": "F",
            "parameters": [
                {
                    "name": "example",
                    "description": "Example parameter",
                    "required": false,
                    "default": false
                }
            ]
        },
        "climate_models": [
            "ACCESS1-0",
            "BNU-ESM",
        ],
        "time_aggregation": "yearly",
        "units": "F",
        "data": {
            "2050": {
                "max": 102.70332763671914,
                "avg": 97.22591587611635,
                "min": 92.67451293945382
            }
        }
    }

Indicator Data Parameters
_________________________

The Indicator object describes all query parameters available for that indicator. An Indicator object is returned by `Indicator list`_ and `Indicator detail`_. Each parameter in the ``Indicator.parameters`` array is an object with the form:

.. json:object:: IndicatorParam

    Definition object for Indicator Data query parameters

    :property string name: The name of the query parameter
    :property string description: A detailed description of how to use the query parameter for indicator data requests, along with its available values if appropriate
    :property boolean required: If true, this query parameter is required
    :property string default: If the query parameter is not required, the default value used when none is provided

These parameters can be used to tweak the `Indicator data`_ request for any indicator.

TODO: Add a note here linking to the example indicator workflow in Overview once that exists.

.. _`contact us`: support@futurefeelslike.com
.. _`Climate Data`: api_reference.html#climate-data
.. _`Indicator list`: api_reference.html#indicator-list
.. _`Indicator detail`: api_reference.html#indicator-detail
.. _`Indicator data`: api_reference.html#indicator-data
.. _`IndicatorParam`: api_reference.html#indicator-data-parameters
.. _`rate-limited`: overview.html#rate-limiting
