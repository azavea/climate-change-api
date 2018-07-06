from django.contrib.gis import admin

from climate_data.models import City


class CityAdmin(admin.GeoModelAdmin):
    # TODO (GH #411): This can be removed when upgrading to Django 1.11
    openlayers_url = 'https://cdnjs.cloudflare.com/ajax/libs/openlayers/2.13.1/OpenLayers.js'

    exclude = ('_geog',)


admin.site.register(City, CityAdmin)
