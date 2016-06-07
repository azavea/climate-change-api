import django_filters
from rest_framework import filters

from climate_data.models import ClimateData


class ClimateDataFilterSet(filters.FilterSet):
    """ Allow min/max/equality filtering on all data fields in ClimateData """
    climate_model = django_filters.CharFilter(name='climate_model__name')
    scenario = django_filters.CharFilter(name='scenario__name')

    min_year = django_filters.NumberFilter(name='year', lookup_type='gte')
    max_year = django_filters.NumberFilter(name='year', lookup_type='lte')

    min_day_of_year = django_filters.NumberFilter(name='day_of_year', lookup_type='gte')
    max_day_of_year = django_filters.NumberFilter(name='day_of_year', lookup_type='lte')

    min_tasmin = django_filters.NumberFilter(name='tasmin', lookup_type='gte')
    max_tasmin = django_filters.NumberFilter(name='tasmin', lookup_type='lte')

    min_tasmax = django_filters.NumberFilter(name='tasmax', lookup_type='gte')
    max_tasmax = django_filters.NumberFilter(name='tasmax', lookup_type='lte')

    min_pr = django_filters.NumberFilter(name='pr', lookup_type='gte')
    max_pr = django_filters.NumberFilter(name='pr', lookup_type='lte')

    class Meta:
        model = ClimateData
        fields = ['climate_model',
                  'year', 'min_year', 'max_year',
                  'day_of_year', 'min_day_of_year', 'max_day_of_year',
                  'tasmin', 'min_tasmin', 'max_tasmin',
                  'tasmax', 'min_tasmax', 'max_tasmax',
                  'pr', 'min_pr', 'max_pr']
