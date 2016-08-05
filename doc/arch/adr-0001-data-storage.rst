Climate Data Storage
====================

Context
-------

This project aims to provide API access to a subset of the NASA NEX Global Daily Downscaled Projection
climate data for points near populated global locations. The source data is very large
(~17TB) and is stored in the NetCDF format. We need to be able to perform the following
operations on the source data:

 - Aggregation of daily values to monthly values
 - Easy filtering for a particular grid cell, scenario, climate model, year and variable
 - Indicator calculations to create derived metrics from the data

We intend to store approximately 10,000 cities worth of data, which will require
up to that many grid cells worth of data stored in the database. This is a significant reduction
from the total ~1 million grid cells in the source data. We would like our solution to be scalable
so that we can store additional cities as the product matures.

Initially, three storage solutions were suggested:


**HDF5 + PyTables**

This solution would essentially allow us to rewrite a subset of the source data to HDF5 files
that store the data in an alternative structure that better suits our use cases. In addition,
the PyTables library provides compression that would significantly reduce the size
of the source data. PyTables also provides a simple filtering ORM that in initial testing would be
sufficient for our use case. There is an HDF5 server that would allow us to directly serve
our converted HDF5 files. Based on initial testing, we could store all of the data for 10,000
cities in ~200Gb, scaled linearly to the number of cities.

There are a few disadvantages to this solution. Aggregation of data is not provided, and would
require a homebuilt solution. The data cannot be sorted by the PyTables API, and so would either
need to be sorted when pulled by the API server process, or before being written to HDF5.
While there is an HDF5 server project, it does not provide an API to allow transformations of
the source data before serving them. As a result, we would need to either fork and extend the
server ourselves, or write a custom web server solution that pulls the source HDF5 files,
transforms them to the necessary output for a particular API response,
and then serves the data. Transformation of data from the source files to whatever format we choose
would require the entire source dataset to be available for a transformer process.


**PostgreSQL**

Storing the data in PostgreSQL provides a few advantages. Aggregation, filtering and sorting of the
data can be done in SQL. It integrates well with the existing Django API that we've written so far,
allowing for management of the tables to be handled via Django. We are generally familiar with the
pros/cons of PostgreSQL and are familiar with ways to optimize it for query speed and general
performance. The import process is more straightforward than the PyTables case, as rows can be
inserted in any order.

The major disadvantage to PostgreSQL is database size. Storing 10,000 cities may require up to 3TB
with some optimization due to the additional overhead and indices required for querying.


**JSON on S3**

This solution would be relatively light on storage space due to the relatively compact format
and available compression.

Disadvantages include requiring that all derived data processing, aggregation and filtering
to be deferred to the client, which significantly reduces our ability to provide value to clients
via an API.


Decision
--------

While a difficult decision, the team decided to move forward with the use of PostgreSQL over
HDF5 + PyTables. Key factors in the decision included familiarity with Django/PostgreSQL, along
with worry about having to implement aggregation/sorting/transformations for the PyTables case.
In addition, we can quickly iterate on the hardware side via AWS RDS.

The team feels more confident in an attempt to squeeze extra performance out of a stack that
they are already familiar with, versus a relative unknown. There is less concern about the size
of the PostgreSQL database versus other disadvantages. The database could be sharded in some
sensible way (e.g. by scenario) so that more cities could be stored across multiple databases.

JSON was not seriously considered due to the static nature of the data, which would require
each client to reimplement aggregation/filtering/sorting which significantly decreases our API's
value proposition.


Consequences
------------

We will almost certainly need to spend time tuning SQL queries in PostgreSQL, and will need to evaluate
performance on an ongoing basis. As we add cities, we will almost certainly need to shard the
database cluster as we bump up against the AWS volume size limit.

HDF5 + PyTables remains a strong contender for future projects where we need to store large
volumes of scientific data. The basic Python libraries (NetCDF and PyTables) are mature and fast.
