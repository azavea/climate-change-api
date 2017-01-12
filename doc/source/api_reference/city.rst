
These endpoints allow users to list, view details of, search and retrieve the boundaries for the locations for which we have climate projections.

A City object is a point feature of the center-most geographic coordinate of an administrative boundary. Each City is associated to a map_cell, a 25 km^2 slice of the Earth's surface. The API breaks up global climate projections by map_cell. Nearby cities, meaning being within the same map_cell, can be expected to experience the same climate.

At this time, only US cities and their climate projection data are available.

.. openapi:: /openapi/climate_api.yml
    :paths: /city/, /city/nearest/, /city/{pk}/, /city/{pk}/boundary/
