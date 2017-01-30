
The Climate Data endpoint allows interaction with annual sets of raw projected temperature and precipitation data for any one city and scenario.

.. note:: Requests to this endpoint are `rate-limited`_.

.. openapi:: /openapi/climate_api.yml
    :paths:
        /climate-data/{city}/{scenario}/

.. _`rate-limited`: overview.html#rate-limiting
