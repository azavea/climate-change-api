import logging

from django.db.models import Q

import django_filters
from rest_framework import filters

from climate_data.models import ClimateData

logger = logging.getLogger(__name__)


class ClimateDataFilterSet(filters.FilterSet):
    """ FilterSet for ClimateData, used by the ClimateData ListAPIView """

    models = django_filters.MethodFilter()
    years = django_filters.MethodFilter()

    def filter_models(self, queryset, value):
        """ Filter models based on a comma separated list of names

        Value should be a string of the form 'climate_model.name,...'

        """
        if value:
            queryset = queryset.filter(climate_model__name__in=value.split(','))
        return queryset

    def filter_years(self, queryset, value):
        """ Filter years based on a list of ranges provided in the query param

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
                    start_year = int(year_range[0])
                    end_year = int(year_range[1])
                    # AND the year range
                    year_filters.append((Q(year__gte=start_year) & Q(year__lte=end_year)))
                if len(year_range) == 1:
                    year = int(year_range[0])
                    year_filters.append(Q(year=year))
            logger.debug(year_filters)
            # Now OR together all the year filters we've created
            queryset = queryset.filter(reduce(lambda x, y: x | y, year_filters))
        return queryset

    class Meta:
        model = ClimateData
        fields = ['models', 'years']
