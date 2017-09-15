Historic Range
--------------

The Historic Range endpoint lists all date ranges whose data is considered to calculate the baseline measure of historic climate. This feature is a reflection of the climatalogical practice to only consider 30 consecutive years of historical data to compare against.


List historic ranges
____________________

.. openapi:: /openapi/climate_api.yml
    :paths:
        /api/historic-range/

Example usage
`````````````

.. code-block:: http

    GET /api/historic-range/ HTTP/1.1
    Host: example.org
    Authorization: Token 46806a08bf54136e9597e879ed3a0876113fdee6

Response:


.. code-block:: http

    HTTP/1.1 200 OK
    Vary: Accept
    Content-Type: application/json

    [
        {
            "start_year": 1951,
            "end_year": 1980
        },
        {
            "start_year": 1961,
            "end_year": 1990
        }
    ]
