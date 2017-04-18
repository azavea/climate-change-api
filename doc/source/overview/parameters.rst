
The API accepts GET, POST, PUT, PATCH, and DELETE HTTP requests.
For GET requests that accept parameters, required parameters are specified in the path. Optional parameters are accepted as HTTP query string parameters::

    https://app.climate.azavea.com/api/climate-data/1/RCP45/indicator/average_high_temperature/?years=2050&units=C

In the above example, '1', 'RCP45', and 'average_high_temperature' are required parameters representing `:city`_, `:scenario`_, and `:indicator`_, while the optional `indicator parameters`_ ``:years`` and ``:units`` are appended in the query string.

For POST, PUT, PATCH, and DELETE requests, parameters not included in the URL should be encoded as JSON in the request body with a Content-Type of 'application/json'.


.. _indicator parameters: api_reference.html#indicator-parameters
.. _:city: api_reference.html#city
.. _:scenario: api_reference.html#scenario
.. _:indicator: api_reference.html#indicator
