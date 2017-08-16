Repository Split
================

Context
-------

As of August 1 2017, we are moving forward in earnest to develop an application in partnership with ICLEI USA, headed on their side by Michael Steinhoff. This application will pull data from our previously built `Climate API <https://climate.azavea.com>`_, but will require additional components that would not make sense as part of the API. For the remainder of this ADR, we will refer to the existing Climate API as the 'Climate API', and the future ICLEI application as the 'ICLEI application'.

We have effectively two options to choose from:

1. Build out the ICLEI application as part of the `Climate API repo <https://github.com/azavea/climate-change-api>`_
2. Begin development of the ICLEI application as a separate repository

There are advantages and disadvantages to each approach. If we were to build the application within the Climate API repository (option 1):

Advantages:

- Faster ICLEI feature iteration. We can immediately use implemented features in the Climate API in the ICLEI application. No need to wait for a deployment of the Climate API to use new features.
- Easier code reuse. If code can be shared between the two applications, then we could potentially iterate faster for features that take advantage of this.

Disadvantages:

- Larger, sprawling codebase that might make it difficult to cleanly distinguish between the Climate API and the ICLEI application in practice
- Larger project management overhead. Conflating issues for both projects into a single GitHub issue tracker has the potential to cause confusion and significant management overhead in keeping all of the tasks and deadlines on track.

In either case, we would likely want to split our deployment stack into a shared pool of resources, e.g. VPC, security groups, database cluster in order to reduce costs, but keep application specific components within the git repository that they serve. If we keep the repositories the same, the split serves to allow us to deploy to a different hostname, if we split the repositories, splitting the deployment stack allows us to reuse some components without duplication.

Decision
--------

We will split the two products into two separate repositories. Our concerns about iteration speed on the two products are not as large as our concerns about being able to cleanly delineate features and task management between the two applications.

We expect to be able to work around problems such as code reuse and multiple deployment environments. Any python code reuse can be broken out via Django apps, and deployment code is relatively standardized at Azavea at this time.

We have plenty of AWS credits remaining, so we are not concerned about the cost of additional AWS resources if the applications are split.

Splitting the applications gives us the opportunity to dogfood our own API, and test it regularly for performance and UX concerns.


Consequences
------------

We expect some friction if any of the following become true:

- Significant code reuse is necessary
- Significant new features are required for the Climate API
- Sunset of the Climate API such that it does not remain a separate, publicly facing product

At this time we are not particularly concerned about any of these items. We expect to require some new Climate API features, but worst case can build most ICLEI app features based on the `Climate Data <https://docs.climate.azavea.com/api_reference.html#climate-data>`_  endpoint of the API. Code reuse would be limited to the Indicator calculations, which are already a separate Django app in the Cimate API project, which would ease this transition.

It's likely that at some point during the development of the ICLEI application, we'll develop a python client for the Climate API. While we could build our own, the `python-azavea-climate <https://github.com/jgcobb3/python-azavea-climate>`_ repo could be used as a starting point.
