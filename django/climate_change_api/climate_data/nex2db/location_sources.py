"""LocationSource methods that map external sources to a list of ClimateLocation tuples.

New sources should define functions or callable classes that perform this mapping.

"""

from collections import namedtuple

""" ClimateLocation

id: A unique id that can be used to identify this ClimateLocation in your dataset
name: A human-readable name used in debug output (optional)
x: Longitude. The value must be between 0-360 (degrees east). e.g. 1 degree W == 359 degrees E
y: Latitude. The value must be between -90 and 90

"""
ClimateLocation = namedtuple('ClimateLocation', ['id', 'name', 'x', 'y'])


def ClimateAPICityLocationSource(city_queryset):
    return [ClimateLocation(id=city.id, x=city.geom.x, y=city.geom.y, name=city.name)
            for city in city_queryset]
