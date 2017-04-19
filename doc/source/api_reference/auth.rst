
The Auth endpoint allows a user to retreive their API token.

Retrieve auth token
___________________
.. openapi:: /openapi/climate_api.yml
    :paths:
        /api-token-auth/

Example usage
`````````````

.. code-block:: http

    POST /api-token-auth/ HTTP/1.1
    Host: example.org
    Content-Type: application/x-www-form-urlencoded
    Content-Length: 40

    email=user%40example.org&password=foobar

Response:

.. code-block:: http

    HTTP/1.1 200 OK
    Vary: Accept
    Content-Type: application/json


    {
        "token": "46806a08bf54136e9597e879ed3a0876113fdee6"
    }
