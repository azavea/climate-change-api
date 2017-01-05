
These endpoints allow users to list, view details of, search and retrieve the boundaries for the locations for which we have climate projections.

A `city` object is a point feature of the center-most geographic coordinate of an administrative boundary. Each city is associated to a `map_cell`, a 25 km^2 slice of the Earth's surface. The API breaks up global climate projections by `map_cell.` Closeby cities, or within the same cell, can be expected to experience the same climate.

At this time, only US cities and their climate projection data are available.

.. openapi:: /openapi/city.yml
