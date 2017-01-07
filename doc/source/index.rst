.. Azavea Climate Data API documentation master file, created by
   sphinx-quickstart on Tue May 24 13:28:42 2016.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Getting Started
===============

.. toctree::
   :maxdepth: 2
   :hidden:

   overview
   api_reference


Logging in
~~~~~~~~~~

**Registration is closed at this time.**

Log in or sign up for a new account with the `Climate API`_.

In addition to API access, all climate API products are accessible with this account.


Getting a token
~~~~~~~~~~~~~~~

Logging in directs you to the Climate API User Profile page, which contains your API token. A valid token is required to make requests to the API. Should you generate a new token, note that your old token will be expired and any instances of it must be updated to access the API.

From the command line, you may request your token by providing the Climate API your account information:

``curl -k -X POST https://staging.api.futurefeelslike.com/api-token-auth/ -d email=<your_email> -d password=<your_password>``


Using the token
~~~~~~~~~~~~~~~
Any API request must be made with an active account token in the request header.

``curl -i https://staging.api.futurefeelslike.com/api/scenario/ -H "Authorization: Token <your_token>"``


Making your first request
~~~~~~~~~~~~~~~~~~~~~~~~~

Voila! With your valid token, you are all set up to make your first API request.


.. URLS:

.. _Climate API: https://staging.api.futurefeelslike.com/accounts/login/
