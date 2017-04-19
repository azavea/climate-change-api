API Documentation
=================

Context
-------

We want to make it convienent for users of our API to have access to good documentation. Up until
this point we have been publishing documentation under `/docs/` with the `rest_framework_swagger`
module. We would like to provide users with more context then a plain swagger UI provides.

We are currently using Sphinx for generating documentation of our internal code. There are
extensions for Sphinx which convert a swagger definition into Sphinx's format for documenting APIs.

Of concern is how the generated documentation will be served to the public and if it should be
versioned. The API itself is not versioned.


Decision
--------

We will use Sphinx to generate API documentation. The build process will download the swagger
definition from a running instance. The Sphinx source will include this swagger definition and
use the the `sphinxcontrib-openapi` extension to read it.

The documentation will be deployed as static sites, for staging and production, outside of the
django application during the build process. The static sites will track the currently
deployed version of the API with no maintainance of old versions, as that documentation will not
be applicable.


Consequences
------------

During testing, the `sphinxcontrib-openapi` extension was not successfully used. Some additional
effort may be necessary to make it work.

If later we decide Sphinx is not a good solution for some reason, the swagger definition should
still be a good intermediate format for generation of documentation.

Because the swagger definition is embedded in a larger body of documentation, context can be given
to the API. Code samples and introductory text, for example, can be included.

We avoid adding too many more dependencies to the project as we are already generating
documentation with Sphinx.

Documentation of historical versions of the API will not be available. There is an assumption
that the API in production will remain stable. If it is not we will want to reassess the decision
not to deploy multiple versions of documentation.
