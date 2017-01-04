Rate Limiting
=============

Context
-------

We want to ensure that the user experience of our API is consistent for as many users as possible. We do not want a small percentage of users abusing the API and reducing performance for all users. In addition, requests to some endpoints of our API are relatively resource-intensive, and have "bursty" access patterns. For example, a user may want to request all temperature data for a few different locations via a script, or request a few different indicators on initial load of the Lab web application. This makes it easier for abuse to occur unintentionally.


Decision
--------

We will apply a sensible global default burst and sustained rate limit via the Django Rest Framework for all user-facing endpoints, that allows for "burst" scenarios but does not allow individual users to abuse the API and negatively impact other users.

Optional adjustments to the default rate limit should be configurable on a per-endpoint basis. If an endpoint does not use the default rate limit, it will be documented via that endpoint's specific documentation.

We will provide a consistent HTTP error code and message when a user is throttled, so that clients can easily handle these errors.


Consequences
------------

Under the normal use cases for this API, we don't believe rate limiting will negatively affect users. Logging rate limiting occurrences will also help us to identify users with high request volumes and reach out to them directly to assist them in tuning their requests.

We will need to monitor our initial rate limits to ensure we are balancing user access with performance. It may be necessary to adjust these limits a few times until we settle on a reasonable global default.

For a subset of higher volume clients who we want to support, it may be necessary to provide user-specific throttling limits. This would not be too difficult via the Django Rest Framework throttling classes.
