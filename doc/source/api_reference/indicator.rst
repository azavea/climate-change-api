
The Indicator endpoints detail all of the derived data "indicators" that are available. The indicators provided by the Climate API are derived quantities generated using the same raw data provided by `Climate Data`_.

If you have ideas for Indicators that aren't provided by the Climate API, but might like to add, please `contact us`_.

Indicator List
______________

.. openapi:: /openapi/climate_api.yml
    :paths:
        /indicator/

Indicator Detail
________________

Detailed information about each indicator. The ``parameters`` attribute of the Indicator response contains an array of `IndicatorParam`_ objects, which provides details about the paramaters that can be sent to the `Indicator data`_ endpoint.

.. openapi:: /openapi/climate_api.yml
    :paths:
        /indicator/{name}/

Indicator Data
______________

Returns data for a specified indicator and its unique required and optional query parameters. See `Indicator detail`_ for more information about these parameters.

.. note:: Requests to this endpoint are `rate-limited`_.

.. openapi:: /openapi/climate_api.yml
    :paths:
        /climate-data/{city}/{scenario}/indicator/{indicator-name}/


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
