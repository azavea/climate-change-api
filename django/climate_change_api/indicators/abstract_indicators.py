from collections import OrderedDict, defaultdict, namedtuple
import re
from datetime import date, timedelta
import calendar

from django.db.models import F, Count, Case, When, CharField, Value

from climate_data.models import ClimateData, ClimateDataSource
from climate_data.filters import ClimateDataFilterSet
from .serializers import IndicatorSerializer


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
        converter = self.getConverter(self.storage_units, self.units)
        for item in aggregations:
            if item['value'] is not None:
                item['value'] = converter(item['value'])
            yield item

    def collate_results(self, aggregations):
        """ Take results as a series of datapoints and collate them by key

        @param aggregations list-of-dicts returned by aggregate method
        @returns Dict of list of values, keyed by the subclass's key_results implementation
        """
        results = defaultdict(list)
        for result in aggregations:
            key = self.key_result(result)
            results[key].append(result['value'])
        return results

    def key_result(self, result):
        """ Stub function for subclasses to determine how to collate results

        @param result A row of timeseries data generated by aggregate()
        @returns The value that row should be keyed by in the final response.
                 Results should be keyed as one of the following based on aggregation:
                 * YYYY for yearly data
                 * YYYY-MM for monthly data
                 * YYYY-MM-DD for daily data
        """
        raise NotImplementedError()

    def calculate(self):
        aggregations = self.aggregate()
        aggregations = self.convert_units(aggregations)
        collations = self.collate_results(aggregations)
        return self.serializer.to_representation(collations)


class YearlyIndicator(Indicator):
    """ Base class for yearly indicators. """

    time_aggregation = 'yearly'

    def key_result(self, result):
        """ Get the row's year for use as a key in collate_results

        @result A row of timeseries data generated by aggregate()
        @returns The year for the result
        """
        return result['data_source__year']


class YearlyAggregationIndicator(YearlyIndicator):
    def aggregate(self):
        return (self.queryset.values('data_source__year', 'data_source__model')
                .annotate(value=self.agg_function(self.variables[0])))


class YearlyCountIndicator(YearlyAggregationIndicator):
    agg_function = Count


class DailyIndicator(Indicator):
    time_aggregation = 'daily'

    def key_result(self, result):
        """ Get the row's date as a Python date object and format as YYYY-MM-DD

        @result A row of timeseries data generated by aggregate()
        @returns The string representation of the date in the format YYYY-MM-DD
        """
        year = result['data_source__year']
        day_of_year = result['day_of_year']
        day = date(year, 1, 1) + timedelta(days=day_of_year-1)
        return day.isoformat()


class DailyRawIndicator(DailyIndicator):
    def aggregate(self):
        variable = self.variables[0]
        return (self.queryset.values('data_source__year', 'day_of_year')
                .annotate(value=F(variable))
                .order_by('data_source__year', 'day_of_year'))


class MonthlyIndicator(Indicator):
    """ Base class for monthly indicators. """

    time_aggregation = 'monthly'

    def key_result(self, result):
        """ Get the row's year and month for use as a key in collate_results

        @result A row of timeseries data generated by aggregate()
        @returns The YYYY-MM for the result
        """
        return '{year}-{mo}'.format(year=result['data_source__year'], mo=result['month'])


class MonthlyAggregationIndicator(MonthlyIndicator):
    MonthRange = namedtuple('MonthRange', ('label', 'start', 'length'))
    range_config = None

    @classmethod
    def get_ranges(cls):
        """ Build mapping from day of year to month.
        Gets the year range by querying what data exists and caches the ranges as a class attribute.
        """
        if cls.range_config is None:
            all_years = set(ClimateDataSource.objects.distinct('year')
                                             .values_list('year', flat=True))
            leap_years = set(filter(calendar.isleap, all_years))
            cls.range_config = {
                'leap': {
                    'years': leap_years,
                    'ranges': [
                        cls.MonthRange('01', 1, 31),
                        cls.MonthRange('02', 32, 29),
                        cls.MonthRange('03', 61, 31),
                        cls.MonthRange('04', 92, 30),
                        cls.MonthRange('05', 122, 31),
                        cls.MonthRange('06', 153, 30),
                        cls.MonthRange('07', 183, 31),
                        cls.MonthRange('08', 214, 31),
                        cls.MonthRange('09', 245, 30),
                        cls.MonthRange('10', 275, 31),
                        cls.MonthRange('11', 306, 30),
                        cls.MonthRange('12', 336, 31),
                    ],
                },
                'nonleap': {
                    'years': all_years - leap_years,
                    'ranges': [
                        cls.MonthRange('01', 1, 31),
                        cls.MonthRange('02', 32, 28),
                        cls.MonthRange('03', 60, 31),
                        cls.MonthRange('04', 91, 30),
                        cls.MonthRange('05', 121, 31),
                        cls.MonthRange('06', 152, 30),
                        cls.MonthRange('07', 182, 31),
                        cls.MonthRange('08', 213, 31),
                        cls.MonthRange('09', 244, 30),
                        cls.MonthRange('10', 274, 31),
                        cls.MonthRange('11', 305, 30),
                        cls.MonthRange('12', 335, 31),
                    ],
                },
            }
        return cls.range_config

    def monthly_case(self):
        """ Generates a nested Case aggregation that assigns the right (zero-padded) month to each
        data point.  It first splits on leap year or not then checks day_of_year against ranges.
        """
        year_whens = []
        for config in self.get_ranges().values():
            month_whens = [When(**{
                'day_of_year__gte': month.start,
                'day_of_year__lte': month.start + month.length,
                'then': Value(month.label)
            }) for month in config['ranges']]
            year_whens.append(When(data_source__year__in=config['years'], then=Case(*month_whens)))
        return Case(*year_whens, output_field=CharField())

    def aggregate(self):
        return (self.queryset.values('data_source__year', 'data_source__model')
                .annotate(month=self.monthly_case())
                .annotate(value=self.agg_function(self.variables[0])))


class MonthlyCountIndicator(MonthlyAggregationIndicator):
    agg_function = Count
