
The Climate Model endpoints describe the models used to generate the temperature and precipitation data provided by the Climate API.

These climate models are provided by a variety of research institutions around the globe, and all follow the `CMIP5 model output specification`_.

Climate Model List
__________________
.. openapi:: /openapi/climate_api.yml
    :paths:
        /api/climate-model/

Example usage
`````````````

.. code-block:: http

    GET /api/climate-model/ HTTP/1.1
    Host: example.org
    Authorization: Token 46806a08bf54136e9597e879ed3a0876113fdee6

Response:

.. code-block:: http

    HTTP/1.1 200 OK
    Vary: Accept
    Content-Type: application/json

    [
        {
            "name": "ACCESS1-0",
            "label": "ACCESS1-0",
            "base_time": null
        },
        {
            "name": "BNU-ESM",
            "label": "BNU-ESM",
            "base_time": null
        }
    ]


Climate Model Detail
____________________
.. openapi:: /openapi/climate_api.yml
    :paths:
        /api/climate-model/{name}/

Example usage
`````````````

.. code-block:: http

    GET /api/climate-model/ACCESS1-0 HTTP/1.1
    Host: example.org
    Authorization: Token 46806a08bf54136e9597e879ed3a0876113fdee6

Response:

.. code-block:: http

    HTTP/1.1 200 OK
    Vary: Accept
    Content-Type: application/json

    {
        "name": "ACCESS1-0",
        "label": "ACCESS1-0",
        "base_time": null
    }

.. _`CMIP5 model output specification`: http://cmip-pcmdi.llnl.gov/cmip5/docs/CMIP5_output_metadata_requirements.pdf
