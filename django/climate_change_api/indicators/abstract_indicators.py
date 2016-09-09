from collections import OrderedDict
import re

from django.db.models import Avg, Count

from climate_data.models import ClimateData
from climate_data.filters import ClimateDataFilterSet
from .serializers import (IndicatorSerializer,
                          DailyIndicatorSerializer)


def float_avg(values):
    return float(sum(values)) / len(values)


def int_avg(values):
    return int(round(float_avg(values)))


class Indicator(object):

    label = ''
    description = ''
    variables = ClimateData.VARIABLE_CHOICES
    filters = None
    serializer_class = IndicatorSerializer

    # Subclasses should use a units mixin from 'unit_converters' to define these units
    # attributes and any necessary conversion functions
    storage_units = None
    default_units = None
    available_units = (None,)

    def __init__(self, city, scenario, models=None, years=None, units=None):
        if not city:
            raise ValueError('Indicator constructor requires a city instance')
        if not scenario:
            raise ValueError('Indicator constructor requires a scenario instance')

        self.city = city
        self.scenario = scenario
        self.models = models
        self.years = years

        # Validate and set desired units
        if units is None:
            self.units = self.default_units
        elif units not in self.available_units:
            raise ValueError('Cannot convert to requested units')
        else:
            self.units = units

        self.queryset = self.get_queryset()
        self.queryset = self.filter_objects()

        self.serializer = self.serializer_class()

    @classmethod
    def name(cls):
        def convert(name):
            """ Convert caps case string to snake case, e.g. IndicatorClass -> indicator_class """
            s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
            return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
        return convert(cls.__name__)

    @classmethod
    def to_dict(cls):
        """ Return a dict representation of the indicator """
        return OrderedDict([
            ('name', cls.name()),
            ('label', cls.label),
            ('description', cls.description),
            ('variables', cls.variables),
            ('avaliable_units', cls.available_units),
            ('default_units', cls.default_units),
        ])

    def get_queryset(self):
        """ Get the initial indicator queryset

        ClimateData initially filtered by city/scenario and optionally years/models as passed
        by the constructor

        """
        filter_set = ClimateDataFilterSet()
        queryset = (ClimateData.objects.filter(map_cell=self.city.map_cell)
                    .filter(data_source__scenario=self.scenario))
        queryset = filter_set.filter_years(queryset, self.years)
        queryset = filter_set.filter_models(queryset, self.models)
        return queryset

    def filter_objects(self):
        """ A subclass can override this to further filter the dataset before calling calculate """
        if self.filters is not None:
            return self.queryset.filter(**self.filters)
        else:
            return self.queryset

    def aggregate(self):
        """ Calculate the indicator aggregation

        This method should use self.queryset to calculate the indicator returning a list of dicts
        that matches the form returned by the Django QuerySet `values` method
        """
        raise NotImplementedError('Indicator subclass must implement aggregate()')

    def convert_units(self, aggregations):
        """ Convert aggregated results to the requested unit.

        @param aggregations list-of-dicts returned by aggregate method
        @returns Dict in same format at results parameter, with values converted to `self.units`
        """
        if self.units == self.storage_units:
            return aggregations
        converter = self.conversions[self.storage_units][self.units]
        for item in aggregations:
            if item['value'] is not None:
                item['value'] = converter(item['value'])
        return aggregations

    def compose_results(self, aggregations):
        """ Combine models and compose results

        Given the results of `aggregate`, should produce a dictionary of the form:
        {
            'year': value
        }
        in the case of yearly aggregated indicators, and
        {
            'year': [jan_value, feb_value,...,dec_value]
        }
        in the case of monthly aggregated indicators
        """
        raise NotImplementedError('Indicator subclass must implement compose_results()')

    def calculate(self):
        aggregations = self.aggregate()
        aggregations = self.convert_units(aggregations)
        results = self.compose_results(aggregations)
        return self.serializer.to_representation(results)


class YearlyIndicator(Indicator):
    """ Base class for yearly indicators. """

    def compose_results(self, aggregations):
        """ Combine models and compose results

        Reduces year/model query results to yearly average, min, and max values across models,
        using floating point values.
        """
        results = {}
        for result in aggregations:
            results.setdefault(result['data_source__year'], []).append(result['value'])
        return {yr: {'avg': float_avg(values), 'min': min(values), 'max': max(values)}
                for (yr, values) in results.items()}


class YearlyAggregationIndicator(YearlyIndicator):
    def aggregate(self):
        return (self.queryset.values('data_source__year', 'data_source__model')
                             .annotate(value=self.agg_function(self.variables[0])))


class YearlyCountIndicator(YearlyAggregationIndicator):
    agg_function = Count

    def compose_results(self, aggregations):
        """ Overriden to return integer values for averages across models """
        results = super(YearlyCountIndicator, self).compose_results(aggregations)
        for (yr, vals) in results.items():
            vals['avg'] = int(round(vals['avg']))
        return results


class DailyIndicator(Indicator):
    serializer_class = DailyIndicatorSerializer


class DailyRawIndicator(DailyIndicator):
    def aggregate(self):
        variable = self.variables[0]
        return (self.queryset.values('data_source__year', 'day_of_year')
                .annotate(value=Avg(variable))
                .order_by('data_source__year', 'day_of_year'))

    def compose_results(self, aggregations):
        return aggregations
