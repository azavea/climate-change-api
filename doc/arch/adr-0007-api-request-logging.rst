API Request Logging
===================

Context
-------

We want to track various metrics about API usage, including:

- Users making requests
- Quantity of requests/user
- Request response time

In order to do so, a few solutions were explored.

(1) Papertrail Nginx log filtering + Librato
________________________________________

This solution entails having Nginx save user-specific information such as the Auth token to the request HTTP headers. Then, request information can be filtered against in Papertrail and sent to Librato via Papertrail's v1 Librato integration.

This solution requires setting up a separate integration for each Librato metric we want to save. There is no way to parameterize the Librato metric name based on regex capture in the Papertrail log message. In an email support chain, Papertrail verified that this is a requested feature and is in the feature backlog for a rewrite of their Librato integration.

*Advantages*:

- Requires no modifications of the API application code
- Fastest time to implement

*Disadvantages*:

- Limited ability to match Papertrail filters to Librato metrics. This is a fairly inflexible solution for now.
- Would need to figure out a way to write a uniquely identifiable string to request headers in Nginx

(2) AWS ALB Logs + S3 + Athena
__________________________

This solution entails saving the AWS ALB logs to S3, and then writing `AWS Athena`_ queries to parse the results. AWS Athena allows logs to be queried via standard SQL, which would allow for extremely flexible metric generation.

Unfortunately, this solution is untenable, as AWS ALB logs do not provide a way for us to map information in the the request headers to unique users in a way that can be saved.

(3) Django Middleware + StatsD + Librato
____________________________________

This solution entails adding a Django middleware layer that pushes our metrics of choice to a statsd implementation (commonly statsite) which then aggregates and pushes those metrics to a 3rd party "sink". Metrics would be available in a near-realtime, queryable and aggregatable web-based dashboard if the Librato sink is chosen. We would need to implement the Django middleware logic, but we have a few examples to work from.

Metrics pushed to Librato can be retrieved via their `Measurements API`_, which would allow us to implement pay-per-use billing or any other feature which requires access to the metrics.

*Advantages*:

- Near-realtime reporting
- No need to write querying/aggregation logic
- Librato "sink" is full featured and fits within budget/usage limits. New "tags" and "computed metrics" features may trivially provide additional insights

*Disadvantages*:

- Requires additional stack infrastructure (statsd daemon)
- Requires additional application code

(4) Django Middleware + PostgreSQL
______________________________

This solution entails saving request details to an activity table in the application database  at the time of the request. Azavea employees would be able to query against it whenever we want to view metrics. Further solutions for automated display of metrics and/or aggregation would require custom logic.

*Advantages*:

- Easy to implement pay-per-use billing in the future
- Extremely flexible

*Disadvantages*:

- Likely the longest time to implement of the options explored
- Limited 3rd-party Django app availability to jumpstart work
- Incurs additional database load for each request

Decision
--------

We will move forward with the solution described by '(3) Django Middleware + StatsD + Librato'. This solution provides us enough flexibility to create our own metrics without coupling too tightly to our application code.

Solution (1) does not provide enough flexibility for our use case and solution (2) is untenable. Solution (4) requires use of our own database, which is something we'd like to avoid for complexity and performance reasons. Solution (4) also requires that we write our own metric aggregation and view code, which slows implementation.

Other projects at Azavea have used various forms of solution (3), which provides a jumping off point with source code and infrastructure examples to draw from. The additional stack infrastructure is a low barrier to entry if we add a `statsite daemon`_ to our existing ECS cluster.

Consequences
------------

This decision felt slightly forced, given that (1) and (2) are essentially untenable as presented. Regardless, the solution presented in (3) is generally robust, using well-vetted external libraries and tools. It also limits the amount of application code we need to modify. The statsite daemon has many options for metric 'sinks', so if Librato becomes a poor fit, switching costs shouldn't be untenable.

The chosen solution does have a few moving parts to link together, but we don't anticipate any major delays in completing the work at this time, as all of the links are documented and we have working examples.


.. _AWS Athena: https://aws.amazon.com/athena/details/
.. _statsite daemon: https://statsite.github.io/statsite/
.. _Measurements API: https://www.librato.com/docs/api/#retrieve-a-measurement
