import logging

from django.db.models import Q

import django_filters
from rest_framework import filters

from climate_data.models import City, ClimateData, ClimateModel
from functools import reduce

logger = logging.getLogger(__name__)


class CityFilterSet(filters.FilterSet):
    """FilterSet for City."""

    admin = django_filters.CharFilter(lookup_expr='icontains')
    name = django_filters.CharFilter(lookup_expr='icontains')
    population_lte = django_filters.NumberFilter(name='population', lookup_expr='lte')
    population_gte = django_filters.NumberFilter(name='population', lookup_expr='gte')
    region = django_filters.NumberFilter()
    search = django_filters.CharFilter(method='filter_search')

    def filter_search(self, queryset, name, value):
        """Custom search param filters on name and admin."""
        return queryset.filter(Q(name__icontains=value) |
                               Q(admin__icontains=value))

    class Meta:
        model = City
        fields = ['admin', 'name', 'population_lte', 'population_gte', 'region', 'search']


class ClimateDataFilterSet(filters.FilterSet):
    """FilterSet for ClimateData, used by the ClimateData ListAPIView."""

    models = django_filters.CharFilter(method='filter_models')
    years = django_filters.CharFilter(method='filter_years')

    def __init__(self, *args, **kwargs):
        self.year_col = kwargs.pop('year_col', 'data_source__year')
        super(ClimateDataFilterSet, self).__init__(*args, **kwargs)

    def filter_models(self, queryset, name, value):
        """Filter models based on a comma separated list of names.

        Value should be a string of the form 'climate_model.name,...'
        """
        if value:
            # Load the models first and then filter on that to avoid scanning
            #  by model names in the final query.
            models = [m.id for m in ClimateModel.objects.filter(name__in=value.split(','))]
            queryset = queryset.filter(data_source__model__id__in=models)
        return queryset

    def filter_years(self, queryset, name, value):
        """Filter years based on a list of ranges provided in the query param.

        Value should be a string of the form: 'start_year[:end_year],...'
        Ranges are inclusive

        Some valid examples:
        2010:2020 - Years 2010 - 2020
        2010,2012,2014 - Years 2010, 2012, 2014 only
        2010:2020,2040:2050,2099 - Years 2010-2020, 2040-2050 and 2099
        """
        if value:
            year_filters = []
            for year_range_str in value.split(','):
                year_range = year_range_str.split(':')
                if len(year_range) == 2:
                    # Pair the two years with their comparators, gte and lte respectively
                    bounds = zip(['gte', 'lte'], year_range)
                    # Create two Q objects with the proper column, comparator and boundary year
                    start, end = [Q(**{"%s__%s" % (self.year_col, comparator): year})
                                  for comparator, year in bounds]
                    # And the checks together
                    year_filters.append(start & end)
                if len(year_range) == 1:
                    year = int(year_range[0])
                    year_filters.append(Q(**{self.year_col: year}))
            logger.debug(year_filters)
            # Now OR together all the year filters we've created
            queryset = queryset.filter(reduce(lambda x, y: x | y, year_filters))
        return queryset

    class Meta:
        model = ClimateData
        fields = ['models', 'years']
