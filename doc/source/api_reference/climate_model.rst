
The Climate Model endpoints describe the models used to generate the temperature and precipitation data provided by the Climate API.

These climate models are provided by a variety of research institutions around the globe, and all follow the `CMIP5 model output specification`_.

Climate Model List
__________________
.. openapi:: /openapi/climate_api.yml
    :paths:
        /api/climate-model/

Climate Model Detail
____________________
.. openapi:: /openapi/climate_api.yml
    :paths:
        /api/climate-model/{name}/

.. _`CMIP5 model output specification`: http://cmip-pcmdi.llnl.gov/cmip5/docs/CMIP5_output_metadata_requirements.pdf
