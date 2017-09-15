Indicator
---------

The Indicator endpoints detail all of the derived data "indicators" that are available. The indicators provided by the Climate API are derived quantities generated using the same raw data provided by `Climate Data`_. For a full list and high-level explanation of indicators, see the `indicators dictionary`_.

To get indicator data, query for the `Indicator list`_, get specific `Indicator params`_ through `Indicator detail`_, and finally customize your `Indicator data`_ request.

If you have ideas for Indicators that aren't provided by the Climate API, but might like to add, please `contact us`_.

Indicator List
______________

Get the full list of indicators from the API.

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

    [
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

Indicator Detail
________________

Get the description and parameters of a specified indicator.

.. openapi:: /openapi/climate_api.yml
    :paths:
        /api/indicator/{indicator_name}/

Example usage
`````````````

.. code-block:: http

    GET /api/indicator/example_temperature_indicator/ HTTP/1.1
    Host: example.org
    Authorization: Token 46806a08bf54136e9597e879ed3a0876113fdee6

Response:

.. code-block:: http

    HTTP/1.1 200 OK
    Vary: Accept
    Content-Type: application/json

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


Indicator Parameters
____________________

Indicator object(s) are returned by `Indicator list`_ and `Indicator detail`_. The Indicator object describes all query parameters available for that indicator. Each parameter in the ``Indicator.parameters`` array is an object with the form:

.. json:object:: IndicatorParam

    Definition object for Indicator query parameters

    :property string name: The name of the query parameter
    :property string description: A detailed description of how to use the query parameter for indicator data requests, along with its available values if appropriate
    :property boolean required: If true, this query parameter is required
    :property string default: If the query parameter is not required, the default value used when none is provided

These parameters can be used to tweak the `Indicator data`_ request for any indicator.

To see this in action, step through `how to make an indicator request`_.


Special Parameters Explained
````````````````````````````

The Climate API allows for various pre-defined and custom types of ``time_aggregation`` when requesting indicator data. Most are familiar, i.e. ``yearly``. A unique format available is ``offset_yearly``, which counts a year starting from the summer solstice (180 days into the Gregorian year). This captures seasons in their entirety, making seasonal analysis easy.


Indicator Data
______________

Returns data for a specified indicator and its unique required and optional query parameters. See `Indicator detail`_ for more information about how to get these parameters.

.. note:: Requests to this endpoint are `rate-limited`_.

.. openapi:: /openapi/climate_api.yml
    :paths:
        /api/climate-data/{city}/{scenario}/indicator/{indicator_name}/

Example usage
`````````````

.. code-block:: http

    GET /api/climate-data/1/RCP85/example_temperature_indicator/ HTTP/1.1
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


.. _`contact us`: climate@azavea.com
.. _`Climate Data`: api_reference.html#climate-data
.. _`Indicator list`: api_reference.html#indicator-list
.. _`Indicator detail`: api_reference.html#indicator-detail
.. _`Indicator data`: api_reference.html#indicator-data
.. _`IndicatorParam`: api_reference.html#indicator-parameters
.. _`Indicator params`: api_reference.html#indicator-parameters
.. _`rate-limited`: overview.html#rate-limiting
.. _`how to make an indicator request`: overview.html#how-to-make-an-indicator-request
.. _`indicators dictionary`: indicators.html
