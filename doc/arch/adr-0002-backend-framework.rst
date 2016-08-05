Backend Framework
=================

Context
-------

The backend framework will be responsible for serving requests from clients, providing
authentication and user profiles, and interfacing with the data storage solution. The team is most
familiar with Django and for this project it is a compelling choice.


Decision
--------

Django was chosen for this project, without strongly considering any other alternatives.
The team's familiarity with Django, along with the Django Rest Framework plugin (DRF) to provide
API views will provide quick iteration on the project. A number of well-maintained plugins to
provide user management and profile views are available to quicly iterate on that aspect of the
application as well.


Consequences
------------

If we are unable to squeeze the necessary performance out of PostgreSQL, we may need to investigate
other solutions for the API portion of the backend framework. However, Django can still be used
to provide user management and authentication.
