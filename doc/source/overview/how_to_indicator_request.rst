
Indicators are channels to interact with the Climate API temperature and precipitation data. There are over a dozen highly parametizable indicators that can be used to answer a broad set of research questions.

Maybe you live in or around Los Angeles, California, a megacity surrounded by farms that experiences signficiant drought. As a land use planner, farmer, utility company, mayor, you're especially interested in preparing for extreme drought. How much drier is it expected to be in LA over the next century?


Get Indicator List
__________________

To begin, `get the full list`_ of actively developed indicators whose response should should look like:


.. code-block:: none

    HTTP/1.1 200 OK
    Vary: Accept
    Content-Type: application/json

    [
        {
            "name": "total_precipitation",
            "label": "Total Precipitation",
            "description": "Total precipitation",
            "valid_aggregations": [
                "yearly",
                "quarterly",
                "monthly",
                "custom"
            ],
            "variables": [
                "pr"
            ],
            "available_units": [
                "mm",
                "kg/m^2",
                "in"
            ],
            "default_units": "in",
            "parameters": [
                {
                    "name": "agg",
                    "description": "A list of comma separated aggregation types to return. Valid choices are 'min', 'max', 'avg', 'median', 'stddev', 'stdev', and 'XXth'. If using 'XXth', replace the XX with a number between 1-99 to return that percentile. For example, '99th' returns the value of the 99th percentile. The 'XXth' option can be provided multiple times with different values. 'stdev' is an alias to 'stddev'. Defaults to 'min,max,avg'.",
                    "required": false,
                    "default": "min,max,avg"
                },
                {
                    "name": "custom_time_agg",
                    "description": "Used in conjunction with the 'custom' time_aggregation value. A list of comma separated month-day pairs defining the time intervals to aggregate within. Data points will only be assigned to one aggregation, and for overlapping intervals the interval defined first will take precedence. Dates are formmatted MM-DD and pairs are formatted 'start:end'. Examples: '3-1:5-31', '1-1:6-30,7-1:12-31'",
                    "required": false
                },
                {
                    "name": "models",
                    "description": "A list of comma separated model names to filter the indicator by. The indicator values in the response will only use the selected models. If not provided, defaults to all models.",
                    "required": false
                },
                {
                    "name": "time_aggregation",
                    "description": "Time granularity to group data by for result structure. Valid aggregations depend on indicator. Can be 'yearly', 'offset_yearly', 'quarterly', 'monthly' or 'custom'. Defaults to 'yearly'. If 'custom', 'custom_time_agg' parameter must be set.",
                    "required": false,
                    "default": "yearly"
                },
                {
                    "name": "units",
                    "description": "Units in which to return the data. Defaults to Imperial units (Fahrenheit for temperature indicators and inches for precipitation).",
                    "required": false,
                    "default": "in"
                },
                {
                    "name": "years",
                    "description": "A list of comma separated year ranges to filter the response by. Defaults to all years available. A year range is of the form 'start[:end]'. Examples: '2010', '2010:2020', '2010:2020,2030', '2010:2020,2030:2040'",
                    "required": false
                }
            ]
        }
        ...
    ]


Each indicator provides a description, parameters, and parameter options. Any special formatting will also be detailed by each param. A closer look at the ``time_aggregation`` parameter of ``total_precipitation`` reveals it defaults to ``yearly`` aggregation, which may be overriden with any of the ``valid_aggregations`` or a user-defined date range for ``custom_time_agg``.


Get Indicator Data
__________________

To access the `indicator data endpoint`_ and retrieve data, we need a city ID, scenario, and indicator. See examples on fetching `city`_ and `scenario`_ info. The indicator is your choice from the previous indicator list request. Since we're investigating drought, we'll look at the ``total_precipitation`` indicator, shown above.

Next, let's use the available parameters to better answer your question. Maybe you'd just like medium and long term annual snapshots, say 2050-2059 and 2090-2099. Maybe you want to prepare for worst and best case scenarios, so you request the minimum and 95th percentile aggregations across models. And maybe you're Canadian, so we'll request the data in metric units.

The three paramaters (city id ``16``, scenario ``RCP85``, and indicator ``total_precipitation``) go directly in the request path::

    /api/climate-data/16/RCP85/indicator/total_precipitation/

The remaining parmeters are appended to the above request as a query string, order agnostic, as ``parameter.name=your_comma_separated_values``. For example, the years 2050-2059, 2090-2099 will be ``years=2050:2059,2090:2099``, the aggregation methods ``agg=min,95th`` and units ``units=mm``. We do not specify the optional parameters whose default values are acceptable. The final request after appending the query parameters to the request:

.. code-block:: http

    GET /api/climate-data/16/RCP85/indicator/total_precipitation/?years=2050:2059,2090:2099&agg=min,95th&units=mm HTTP/1.1
    Host: example.org
    Authorization: Token 46806a08bf54136e9597e879ed3a0876113fdee6


Response:

    Note -- for brevity, some sections of the mock response have been replaced with ellipses.

.. code-block:: none

    HTTP/1.1 200 OK
    Vary: Accept
    Content-Type: application/json

    {
        "city": {...},
        "scenario": "RCP85",
        "indicator": {...},
        "climate_models": [...],
        "time_aggregation": "yearly",
        "units": "mm",
        "data": {
            "2050": {
                "95th": 502.14717722977383,
                "min": 76.3011513440915
            },
            "2051": {
                "95th": 422.72801741558726,
                "min": 87.7231065219347
            },
            "2052": {
                "95th": 384.35449249837097,
                "min": 69.0049433681225
            },
            "2053": {
                "95th": 400.43015853959912,
                "min": 71.0826842037477
            },
            "2054": {
                "95th": 309.52329147214721,
                "min": 85.7466253202801
            },
            "2055": {
                "95th": 319.07056730291276,
                "min": 43.0824827632023
            },
            "2056": {
                "95th": 355.2163854523539,
                "min": 30.477575477812
            },
            "2057": {
                "95th": 480.81317679456305,
                "min": 78.5377983238959
            },
            "2058": {
                "95th": 398.13347491573677,
                "min": 36.2675766097709
            },
            "2059": {
                "95th": 494.23366352905958,
                "min": 33.8631876410659
            },
            "2092": {
                "95th": 490.50283861029754,
                "min": 66.9922689942837
            },
            "2093": {
                "95th": 476.07359825991239,
                "min": 57.4320739849099
            },
            "2094": {
                "95th": 541.81907089825916,
                "min": 41.4477364907725
            },
            "2095": {
                "95th": 452.86661269688466,
                "min": 100.000476022296
            },
            "2096": {
                "95th": 326.26334963959147,
                "min": 96.7786111861642
            },
            "2091": {
                "95th": 473.53951300371136,
                "min": 29.6483782503742
            },
            "2098": {
                "95th": 489.71526518822668,
                "min": 30.6247628551318
            },
            "2099": {
                "95th": 418.83536519337997,
                "min": 122.807143095861
            },
            "2097": {
                "95th": 397.18454635143212,
                "min": 47.4329927169493
            },
            "2090": {
                "95th": 497.58873546250254,
                "min": 54.6301852183661
            }
        }
    }

Success! To answer our question, we can expect continued, consistent drought mid century and noteworthy turbulence to the norm in precipitation end of century. Notwithstanding, Los Angeles can expect its current drought patterns to be a fairly good measure for future planning. Now that you've successfully made this request, consider adjusting the parameters yourself on ``total_precipitation`` or query other indicators to get more perspectives on precipitation to further explore drought in Los Angeles.


.. _get the full list: api_reference.html#indicator-list
.. _indicator data endpoint: api_reference.html#indicator-data
.. _city: api_reference.html#nearest-city-or-cities
.. _scenario: api_reference.html#scenario-list
