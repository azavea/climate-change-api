
These endpoints allow users to list, view details of, search, and retrieve the boundaries for the locations for which we have climate projections.

A Region object is a multipolygon feature of an ecoregion.

List Regions
____________
.. openapi:: /openapi/climate_api.yml
    :paths:
        /api/region/

Example usage
`````````````

.. code-block:: http

    GET /api/region/ HTTP/1.1
    Host: example.org
    Authorization: Token 46806a08bf54136e9597e879ed3a0876113fdee6

Response:

.. code-block:: http

    HTTP/1.1 200 OK
    Vary: Accept
    Content-Type: application/json

    {
        "count": 51,
        "next": "http://example.org/api/region/?offset=1",
        "previous": null,
        "results": [
            {
                "id": 1,
                "level1": 12,
                "level1_description": "SOUTHERN SEMIARID HIGHLANDS",
                "level2": 1,
                "level2_description": "WESTERN SIERRA MADRE PIEDMONT"
            }
        ]
    }

Request region
______________
.. openapi:: /openapi/climate_api.yml
    :paths:
        /api/region/{pk}/

Example usage
`````````````

.. code-block:: http

    GET /api/region/30/ HTTP/1.1
    Host: example.org
    Authorization: Token 46806a08bf54136e9597e879ed3a0876113fdee6

Response:

.. code-block:: http

    HTTP/1.1 200 OK
    Vary: Accept
    Content-Type: application/json

    {
        "geometry": {
            "coordinates": [
                [
                    [
                        [
                            -109.78794642794765,
                            24.150443522643897
                        ],
                        [
                            -109.79081866386304,
                            24.139997712991548
                        ],
                    ]
                ],
                [
                    [
                        [
                            -110.13559035042405,
                            24.241837359104423
                        ],
                        [
                            -110.08459913211541,
                            24.2138681608711
                        ],
                    ]
                ]
            ],
            "type": "MultiPolygon"
        },
        "id": 30,
        "properties": {
            "level1": 14,
            "level1_description": "TROPICAL DRY FORESTS",
            "level2": 6,
            "level2_description": "SIERRA AND PLAINS OF EL CABO"
        },
        "type": "Feature"
    }
