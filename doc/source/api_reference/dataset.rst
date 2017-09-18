Dataset
-------

The Climate Dataset endpoints describe the datasets available in the Climate API. Currently the API serves data from two datasets:

 - `NASA NEX-GDDP`_
 - `UCSD LOCA`_

The "name" attribute of a dataset response can be used in other requests to specify which dataset to source results from.


Climate Dataset List
____________________
.. openapi:: /openapi/climate_api.yml
    :paths:
        /api/dataset/

Example usage
`````````````

.. code-block:: http

    GET /api/dataset/ HTTP/1.1
    Host: example.org
    Authorization: Token 46806a08bf54136e9597e879ed3a0876113fdee6

Response:

.. code-block:: http

    HTTP/1.1 200 OK
    Vary: Accept
    Content-Type: application/json

    [
        {
            "name": "NEX-GDDP",
            "label": "Nasa Earth Exchange Global Daily Downscaled Projections",
            "description": "The NASA Earth Exchange (NEX) Global Daily Downscaled Projections (NEX-GDDP) dataset is comprised of downscaled climate scenarios that are derived from the General Circulation Model (GCM) runs...",
            "url": "https://nex.nasa.gov/nex/projects/1356/",
            "models": [
                "ACCESS1-0",
                "BNU-ESM",
                "CCSM4",
                "..."
            ]
        }, {
            "name": "LOCA",
            "label": "Localized Constructed Analogs Downscaled Projections",
            "description": "The LOCA (Localized Constructed Analogs) dataset includes downscaled projections from 32 global climate models calculated for two Representative Concentration Pathways (RCP 4.5 and RCP 8.5). Each of the climate projections includes daily maximum temperature, minimum temperature, and precipitation for every 6x6km (1/16th degree resolution) for the conterminous US from 1950 to 2100. LOCA attempts to better preserve extreme hot days, heavy rain events and regional patterns of precipitation. The total dataset size is approximately 10 TB.",
            "url": "http://loca.ucsd.edu/",
            "models": [
                "ACCESS1-0",
                "ACCESS1-3",
                "CCSM4",
                "..."
            ]
        }
    ]


Climate Dataset Detail
______________________
.. openapi:: /openapi/climate_api.yml
    :paths:
        /api/dataset/{name}/

Example usage
`````````````

.. code-block:: http

    GET /api/dataset/LOCA/ HTTP/1.1
    Host: example.org
    Authorization: Token 46806a08bf54136e9597e879ed3a0876113fdee6

Response:

.. code-block:: http

    HTTP/1.1 200 OK
    Vary: Accept
    Content-Type: application/json

    {
        "name": "NEX-GDDP",
        "label": "Nasa Earth Exchange Global Daily Downscaled Projections",
        "description": "The NASA Earth Exchange (NEX) Global Daily Downscaled Projections (NEX-GDDP) dataset is comprised of downscaled climate scenarios that are derived from the General Circulation Model (GCM) runs...",
        "url": "https://nex.nasa.gov/nex/projects/1356/",
        "models": [
            "ACCESS1-0",
            "BNU-ESM",
            "CCSM4",
            "CESM1-BGC"
        ]
    }

.. _`NASA NEX-GDDP`: https://cds.nccs.nasa.gov/nex-gddp/
.. _`UCSD LOCA`: http://loca.ucsd.edu/
