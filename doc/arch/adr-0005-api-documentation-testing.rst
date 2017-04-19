API Documentation Testing
=========================

Supercedes `ADR 0004`_.


Context
-------

We want to ensure that the API documentation and the public API surface remain consistent. In `ADR 0004`_ we decided to "download the Swagger definition from a running instance, and include that definition in the Sphinx source". After further experimentation and a bit of development, there are a few issues with this approach:

- Newer versions of the django-rest-swagger plugin, responsible for autogenerating the swagger spec, have removed support for inline documentation, preferring to couple tightly to the new Schema_ features introduced to Django Rest Framework 3.5. If we were to use the new Schemas feature, we'd be tying ourselves to a relatively new, somewhat untested feature that doesn't necessarily directly align with our goals, which requires significant boilerplate in the Django code and is unable to document any parts of the API that may exist outside Django
- Currently our API documentation (endpoints, parameters, URLS) are scattered in a few places.
- We need to write tooling that auto-detects all of our endpoints, downloads the Swagger JSON definitions, converts them to YAML and copies them to the Sphinx folders

An alternative approach, described below, would allow for the following:
- All documentation in one place (the Sphinx docs)
- A CI job which validates the format and functionality of the actual API against its docs to ensure they remain in sync, via `Dredd`_


Decision
--------

We will modify our Sphinx documentation to do the following:
- All API documentation will be written in Sphinx rst for general prose
- The API definition will be written in YAML using the Swagger 2.0 API specification
- On each merge to develop, a CI job will run which will validate the API described by the documentation against a running local instance of the API, via `Dredd`_

An alternative API documentation format was evaluated: `API Blueprint`_. This API documentation format is less verbose but is not written in a widely available machine readable format (JSON/YAML). It does not appear to offer any significant advantages, and we are already more familiar with Swagger.


Consequences
------------

We will need to take the time to initially write all of our Swagger API specifications from scratch. There are some tools provided by Swagger that should make this process relatively easy, even if it is time consuming.

Initially, we intended for the Swagger YAML spec to be split across multiple files and be inlined into the prose documentation at relevant points. However, a few technical challenges prevented this, and instead we will move forward with the entire spec within one YAML file. The issues we ran into are outlined in `PR 221`_.

We will also need to install and configure `Dredd`_ for our development and CI environments.


.. _ADR 0004: doc/arch/adr-0004-api-documentation.rst
.. _Dredd: https://github.com/apiaryio/dredd
.. _PR 221: https://github.com/azavea/climate-change-api/pull/221
.. _Schemas: http://www.django-rest-framework.org/api-guide/schemas
.. _sphinxcontrib openapi: https://github.com/ikalnytskyi/sphinxcontrib-openapi
