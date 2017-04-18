
All requests to the Climate API must be authenticated. The Climate API supports the Token authentication scheme via HTTP header.

Your token must be provided in the ``Authorization`` HTTP header with every request. The key should be prefixed by the string literal ``Token``, with whitespace separating the two strings::

    Authorization: Token <your token here>

Guard your API token carefully. If compromised, you can generate a new one by going to your `Profile`_. When you regenerate your token, applications using your old token will cease to operate.

Your token can be found in your `Profile`_ while logged in, or by making a POST request to `/api-token-auth/`_.

.. _Profile: https://app.climate.azavea.com/accounts/profile/
.. _/api-token-auth/: api_reference.html#auth
