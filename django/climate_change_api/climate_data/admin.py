from django.contrib import admin

from climate_data.models import City


class CityAdmin(admin.ModelAdmin):
    exclude = ('_geog',)


admin.site.register(City, CityAdmin)
