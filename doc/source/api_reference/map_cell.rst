Map cells
---------

The API breaks up global climate projections by Map Cell. Each Map Cell, when combined with a dataset, represents a slice of the geographic area of the underlying climate dataset. For example, each LOCA Map Cell represents a 1/16 degree box. As data returned by the API is calculated by Map Cell, points or Cities within the same Map Cell will return the same data.

Each Map Cell may be associated with a number of City objects.

At this time, only US cities are present in the API, but we may have non-US Map
Cells available if you query by latitude and longitude instead of City.


Get map cells
__________________

This endpoint exposes the underlying grid points used for each dataset. A grid point maps to a grid cell from the source NetCDF dataset.

Retrieve all available map cells for a given Lat + Lon, as well as all map cells
within an optional distance parameter, specified in meters.

Returned Map Cells are ordered based on their distance to the provided Lat
+ Lon.

Note that the longitude returned was previously in the range [0, 360), which aligns with the source NetCDF dataset, but it has been changed to be in the range [-180, 180) so that the response represents valid GeoJSON in EPSG:4326.

.. openapi:: /openapi/climate_api.yml
    :paths:
        /api/map-cell/{lat}/{lon}/

Example usage
`````````````

.. code-block:: http

    GET /api/map-cell/0/0/map-cell/?distance=10000 HTTP/1.1
    Host: example.org
    Authorization: Token 46806a08bf54136e9597e879ed3a0876113fdee6

Response:

.. code-block:: http

    HTTP/1.1 200 OK
    Vary: Accept
    Content-Type: application/json

    [
        {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [0, 0]
            },
            "properties": {
                "datasets": ["LOCA", "NEX-GDDP"],
                "distance_meters": 4321,
                "proximity": {
                    "ocean": true
                }
            }
        }, {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [1.23, 4.56]
            },
            "properties": {
                "datasets": ["NEX-GDDP"],
                "distance_meters": 7654,
                "proximity": {
                    "ocean": false
                }
            }
        }
    ]
