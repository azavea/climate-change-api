
The Climate API uses HTTP codes to indicate a successful, failed, or unsupported request. These codes follow the standards defined in |RFC 7231| and more information about any response codes (Including the meaning for codes not mentioned here) can be found there. Below is a list of the most common response codes and what they mean for this API specifically.

200 OK
______
The request was completed successfully. The response will include a payload with an object containing the requested data based on what API endpoint was requested.

400 Bad Request
_______________
The requested endpoint was found, but there was a problem with the query parameters - they may have been in an unexpected format, or asked for something that the API cannot do. The response will include an error message with the invalid parameter and what its expected values are.

404 Not Found
_____________
The requested data does not exist - either the URI doesn't match an API endpoint, or the API couldn't find the object referenced by a path parameter. If the URI matched a multi-parameter API action, the response will include a message detailing which parameter wasn't found. Otherwise, check the spelling or consult the `API Reference`_ for the path to use for the intended endpoint.

429 Too Many Requests
_____________________
The rate of user requests exceeded API rate limits - check the error response for details explaining how to proceed. Consult the `API Reference`_ for greater detail.


.. |RFC 7231| raw:: html

    <a href="https://tools.ietf.org/html/rfc7231.html" target="_blank">RFC 7231</a>

.. _`API Reference`: api_reference.html
