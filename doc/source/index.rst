.. Azavea Climate API documentation master file, created by
   sphinx-quickstart on Tue May 24 13:28:42 2016.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

.. toctree::
   :maxdepth: 2
   :hidden:

   self
   overview
   api_reference
   indicators


Getting Started
===============

The global climate is changing. Seasons are shifting. Sea levels are rising. Extreme climatic events are becoming more frequent and more intense. Every day more people and institutions are trying to respond and prepare effectively.

Everyone has climate questions. For example, how will my area be affected? With what probability can these changes be expected? How will the growing season shift? Can I access and afford reliable climate projection data?

The National Aeronautics and Space Administration of the United States (NASA) produces an abundance of quality global climate data available in NEX format. Recognizing that this more unique data format limits accessibility for many climate professionals, scientists, and even citizens who are actively preparing for climate change, the Climate API processes the NEX data according to the standards set by the Intergovernmental Panel on Climate Change (`IPCC`_) and serves it in the universal format, `JSON`_. `JSON`_ is a data structure accepted by virtually all modern programming languages.

Currently, the Climate API includes temperature and precipitation data for cities across the entire USA historically and under two popular carbon emission scenarios projected until the end of the century.

Accessible and standardized climate data through the Climate API will help answer decision makers, scientists, technologists, and citizens to answer the aforementioned questions and more. Read on to learn how to use the API.


Logging in
~~~~~~~~~~

`Log in`_ or `sign up`_ for a new account with the Climate API.


Getting a token
~~~~~~~~~~~~~~~

`Logging in`_ directs you to the Climate API User Profile page, which contains your API token. A valid token is required to make requests to the API. Should you generate a new token, note that your old token will be expired and any instances of it must be updated to access the API.

From the command line, you may request your token by providing the Climate API `your account`_ information::

    curl -k -X POST https://app.climate.azavea.com/api-token-auth/ -d email=<your_email> -d password=<your_password>


Making your first request
~~~~~~~~~~~~~~~~~~~~~~~~~
Any API request must be made with an active account token in the request header::

    curl -i https://app.climate.azavea.com/api/scenario/ -H "Authorization: Token <your_token>"

Voila! You've just make your first Climate API request.


.. URLS:

.. _JSON: https://msdn.microsoft.com/en-us/library/bb299886.aspx
.. _Log in: https://app.climate.azavea.com/accounts/login/
.. _Logging in: https://app.climate.azavea.com/accounts/login/
.. _sign up: https://app.climate.azavea.com/accounts/register/
.. _IPCC: https://www.ipcc.ch/index.htm
.. _your account: https://app.climate.azavea.com/accounts/profile/
