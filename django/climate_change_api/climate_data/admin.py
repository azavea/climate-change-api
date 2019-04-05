from django.contrib.gis import admin

from climate_data.models import City


class CityAdmin(admin.GeoModelAdmin):
    exclude = ('_geog',)


admin.site.register(City, CityAdmin)
