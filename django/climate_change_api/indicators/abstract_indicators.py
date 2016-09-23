from collections import OrderedDict, defaultdict
import re
from datetime import date, timedelta

from django.db.models import F, Avg, Count

from climate_data.models import ClimateData
from climate_data.filters import ClimateDataFilterSet
from .serializers import IndicatorSerializer


def float_avg(values):
    return float(sum(values)) / len(values)


def int_avg(values):
    return int(round(float_avg(values)))


class Indicator(object):

    label = ''
    description = ''
    time_aggregation = None     # One of 'daily'|'monthly'|'yearly'
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

        # Set and validate desired units
        self.units = units if units is not None else self.default_units
        if self.units not in self.available_units:
            raise ValueError('Cannot convert to requested units ({})'.format(self.units))

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
            ('time_aggregation', cls.time_aggregation),
            ('variables', cls.variables),
            ('available_units', cls.available_units),
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

        This method should use self.queryset to calculate the indicator, returning a list of dicts
        that matches the form returned by the Django QuerySet `values` method and includes the
        target value under the 'value' key.
        e.g. { 'data_source__year': 2077, 'data_source__model': 4, 'value': 74.59}
        """
        raise NotImplementedError('Indicator subclass must implement aggregate()')

    def convert_units(self, aggregations):
        """ Convert aggregated results to the requested unit.

        @param aggregations list-of-dicts returned by aggregate method
        @returns Dict in same format as the aggregations parameter, with values converted
                 to `self.units`
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
            'time_repr': {'avg': value, 'min': value, 'max': value}
        }

        Where 'time_repr' is the date in a hyphen-deliminated ISO-8601 format for
        the appropriate aggregation level. Specifically, one of the following:
        * YYYY for yearly data
        * YYYY-MM for monthly data
        * YYYY-MM-DD for daily data

        _Do not_ use YYYYMMDD

        For example, a yearly indicator could be presented as:
        {
            '2050': {'avg': value, 'min': value, 'max': value}
        }

        And a monthly indicator as:
        {
            '2050-03': {'avg': value, 'min': value, 'max': value}
        }

        """
        return {key: {'avg': float_avg(values), 'min': min(values), 'max': max(values)}
                for (key, values) in aggregations.iteritems()}

    def calculate(self):
        aggregations = self.aggregate()
        aggregations = self.convert_units(aggregations)
        collations = self.collate_results(aggregations)
        results = self.compose_results(collations)
        return self.serializer.to_representation(results)


class YearlyIndicator(Indicator):
    """ Base class for yearly indicators. """

    time_aggregation = 'yearly'

    def collate_results(self, aggregations):
        results = defaultdict(list)
        for result in aggregations:
            results[result['data_source__year']].append(result['value'])
        return results


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
    time_aggregation = 'daily'

    def collate_results(self, aggregations):
        # Convert the timeseries data into a more easily digestible tuple format
        # The list is already sorted, so we can just maintain the original order
        tuple_list = ((d['data_source__year'], d['day_of_year'], d['value'])
                     for d in aggregations if d['value'])

        results = defaultdict(list)
        for (year, day_of_year, value) in tuple_list:
            # Convert year and day_of_year to a Python date object
            day = date(year, 1, 1) + timedelta(days=day_of_year-1)
            results[day.isoformat()].append(value)
        return results


class DailyRawIndicator(DailyIndicator):
    def aggregate(self):
        variable = self.variables[0]
        return (self.queryset.values('data_source__year', 'day_of_year')
                .annotate(value=F(variable))
                .order_by('data_source__year', 'day_of_year'))
