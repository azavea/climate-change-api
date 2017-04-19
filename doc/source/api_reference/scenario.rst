
The Scenario endpoints describe the Representative Concentration Pathways (RCPs) defined by the `fifth IPCC Assessment Report`_ that this API supports.

These RCPs define greenhouse gas concentrations over time based upon a few different future scenarios of anthropogenic (human-caused) greenhouse gas emissions.

Scenario List
_____________
.. openapi:: /openapi/climate_api.yml
    :paths:
        /api/scenario/

Example usage
`````````````

.. code-block:: http

    GET /api/scenario/ HTTP/1.1
    Host: example.org
    Authorization: Token 46806a08bf54136e9597e879ed3a0876113fdee6

Response:

.. code-block:: http

    HTTP/1.1 200 OK
    Vary: Accept
    Content-Type: application/json


    [
        {
            "name": "RCP85",
            "label": "RCP 8.5",
            "description": "Rising radiative forcing pathway leading to 8.5 W/m2 in 2100. See https://www.skepticalscience.com/rcp.php"
        },
        {
            "name": "historical",
            "label": "Historical",
            "description": "A historical dataset from NEX GDDP for 1950 to 2005 that blends reanalysis data with observations"
        }
    ]

Scenario Detail
_______________
.. openapi:: /openapi/climate_api.yml
    :paths:
        /api/scenario/{name}/

Example usage
`````````````

.. code-block:: http

    GET /api/scenario/RCP85/ HTTP/1.1
    Host: example.org
    Authorization: Token 46806a08bf54136e9597e879ed3a0876113fdee6


Response:

.. code-block:: http

    HTTP/1.1 200 OK
    Vary: Accept
    Content-Type: application/json

    {
      "name": "RCP85",
      "label": "RCP 8.5",
      "description": "Rising radiative forcing pathway leading to 8.5 W/m2 in 2100. See https://www.skepticalscience.com/rcp.php"
    }

.. _`fifth IPCC Assessment Report`: https://en.wikipedia.org/wiki/IPCC_Fifth_Assessment_Report
