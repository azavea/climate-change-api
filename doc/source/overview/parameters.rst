
The API accepts GET, POST, PUT, PATCH, and DELETE HTTP requests.
For GET requests that accept parameters, required parameters are specified in the path. Optional parameters are accepted as an HTTP query string parameter::

    https://api.futurefeelslike.com/api/climate-data/1/RCP45/indicator/average_high_temperature/?years=2050&units=C

Above, '1', 'RCP45', and 'average_high_temperature' are required parameters representing ``:city``, ``:scenario``, and ``:indicator`` while the optional parameters ``:years`` and ``:units`` are appended in the query string.

For POST, PUT, PATCH, and DELETE requests, parameters not included in the URL should be encoded as JSON in the request body with a Content-Type of 'application/json'.