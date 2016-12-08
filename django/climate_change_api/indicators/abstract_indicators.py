from collections import OrderedDict, defaultdict, namedtuple
from itertools import groupby
import re
from datetime import date, timedelta
import calendar

from django.db.models import F, Case, When, CharField, FloatField, Value, Sum
from django.db import connection


from climate_data.models import ClimateData, ClimateDataSource
from climate_data.filters import ClimateDataFilterSet
from .serializers import IndicatorSerializer
from .unit_converters import DaysUnitsMixin, TemperatureConverter


MonthRange = namedtuple('MonthRange', ('label', 'start', 'length'))


class Indicator(object):

    label = ''
    description = ''
    time_aggregation = None     # One of 'daily'|'monthly'|'yearly'
    valid_aggregations = ('yearly', 'monthly', 'daily', )
    variables = ClimateData.VARIABLE_CHOICES

    # Filters define which rows match our query, conditions limit which rows
    # within that set fit the criteria. That is, if a filter excludes a row it is
    # completely ignored, but if a condition excludes a row it is replaced with a
    # default value.
    # This enables us to provide a value for timespans that have no matching
    # periods, but is imperfect and only works for aggregations where a default
    # value makes sense.
    filters = None
    conditions = None
    agg_function = F
    default_value = 0

    serializer_class = IndicatorSerializer

    # Subclasses should use a units mixin from 'unit_converters' to define these units
    # attributes and any necessary conversion functions
    storage_units = None
    default_units = None
    available_units = (None,)
    parameters = None

    monthly_range_config = None

    def __init__(self, city, scenario, models=None, years=None, time_aggregation=None,
                 serializer_aggregations=None, units=None, parameters=None):
        if not city:
            raise ValueError('Indicator constructor requires a city instance')
        if not scenario:
            raise ValueError('Indicator constructor requires a scenario instance')

        self.city = city
        self.scenario = scenario
        self.models = models
        self.years = years
        self.serializer_aggregations = serializer_aggregations

        # Set and validate desired units
        self.units = units if units is not None else self.default_units
        if self.units not in self.available_units:
            raise ValueError('Cannot convert to requested units ({})'.format(self.units))

        if self.parameters is not None:
            # Because degree days changes the parameters object, we need to make sure we make a copy
            parameters = parameters if parameters is not None else {}
            self.parameters = {key: parameters.get(key, default)
                               for (key, default) in self.parameters.items()}

        self.time_aggregation = (time_aggregation if time_aggregation is not None
                                 else self.valid_aggregations[0])
        if self.time_aggregation not in self.valid_aggregations:
            raise ValueError('Cannot aggregate indicator by requested interval ({})'
                             .format(self.time_aggregation))

        self.queryset = self.get_queryset()

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

        if self.filters is not None:
            queryset = queryset.filter(**self.filters)

        if self.time_aggregation == 'monthly':
            queryset = queryset.annotate(month=self.monthly_case())

        return queryset

    @classmethod
    def get_monthly_ranges(cls):
        """ Build mapping from day of year to month.

        Gets the year range by querying what data exists and builds MonthRange objects for each
        month.

        Caches the resulting range config as a class attribute.
        """
        if cls.monthly_range_config is None:
            all_years = set(ClimateDataSource.objects.distinct('year')
                                             .values_list('year', flat=True))
            leap_years = set(filter(calendar.isleap, all_years))

            def make_ranges(months):
                return [MonthRange('{:02d}'.format(i+1), sum(months[:i])+1, months[i])
                        for i in range(len(months))]

            cls.monthly_range_config = {
                'leap': {
                    'years': leap_years,
                    'ranges': make_ranges([31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]),
                },
                'nonleap': {
                    'years': all_years - leap_years,
                    'ranges': make_ranges([31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]),
                },
            }
        return cls.monthly_range_config

    def monthly_case(self):
        """ Generates a nested Case aggregation that assigns the right (zero-padded) month to each
        data point.  It first splits on leap year or not then checks day_of_year against ranges.
        """
        year_whens = []
        for config in self.get_monthly_ranges().values():
            month_whens = [When(**{
                'day_of_year__gte': month.start,
                'day_of_year__lte': month.start + month.length,
                'then': Value(month.label)
            }) for month in config['ranges']]
            year_whens.append(When(data_source__year__in=config['years'], then=Case(*month_whens)))
        return Case(*year_whens, output_field=CharField())

    @property
    def aggregate_keys(self):
        return {
            'daily': ['data_source__year', 'day_of_year', 'data_source__model'],
            'monthly': ['data_source__year', 'month', 'data_source__model'],
            'yearly': ['data_source__year', 'data_source__model']
        }.get(self.time_aggregation)

    @property
    def expression(self):
        return self.variables[0]

    def aggregate(self):
        """ Calculate the indicator aggregation

        This method should use self.queryset to calculate the indicator, returning a list of dicts
        that matches the form returned by the Django QuerySet `values` method and includes the
        target value under the 'value' key.
        e.g. { 'data_source__year': 2077, 'data_source__model': 4, 'value': 74.59}
        """

        if self.conditions:
            agg_function = self.agg_function(Case(When(then=self.expression, **self.conditions),
                                             default=self.default_value,
                                             output_field=FloatField()))
        else:
            agg_function = self.agg_function(self.expression)

        return (self.queryset.values(*self.aggregate_keys).annotate(value=agg_function))

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
        year = result['data_source__year']
        if self.time_aggregation == 'yearly':
            return year

        if self.time_aggregation == 'monthly':
            month = result['month']
            return '{year}-{mo}'.format(year=year, mo=month)

        if self.time_aggregation == 'daily':
            day_of_year = result['day_of_year']
            day = date(year, 1, 1) + timedelta(days=day_of_year-1)
            return day.isoformat()

    def calculate(self):
        aggregations = self.aggregate()
        aggregations = self.convert_units(aggregations)
        collations = self.collate_results(aggregations)
        return self.serializer.to_representation(collations,
                                                 aggregations=self.serializer_aggregations)


class CountIndicator(Indicator):
    """ Class to count days on which a condition is met.

    Essentially a specialized version of the YearlyAggregationIndicator where all values count as 1
    if they match the conditions and 0 in all other cases.
    """
    agg_function = Sum
    expression = 1


class YearlySequenceIndicator(CountIndicator):
    """ Abstract indicator to count series of consecutive days on which a condition is met.

    The query is done with raw SQL, so the condition has to be a string that constitutes a
    valid condition when dropped into the WHEN clause inside the query.
    """

    valid_aggregations = ('yearly',)

    def get_streaks(self):
        """
        Uses a query to partition the data series into consecutive days on which the condition is
        or is not met and return all the streaks sorted by year and model.

        Starts from the existing queryset with year/model/etc filters already applied.

        Returns non-matching as well as matching sequences to guarantee that any year that matches
        the filter parameters and for which we have data will be represented in the results set.
        Filtering out non-matches inside the query would mean we get no results for years with no
        matches, making them indistinguishable from years that were filtered out or for which
        there is no data.
        """
        (base_query, base_query_params) = (self.queryset.select_related('data_source')
                                               .query.sql_with_params())
        query = """
            SELECT year as data_source__year, model_id as data_source__model,
                   count(*) as length, match
            FROM (SELECT year, model_id, day_of_year,
                         (CASE WHEN {condition} THEN 1 ELSE 0 END) as match,
                         ROW_NUMBER() OVER(ORDER BY year, model_id, day_of_year) -
                         ROW_NUMBER() OVER(PARTITION BY CASE WHEN {condition} THEN 1 ELSE 0 END
                                           ORDER BY year, model_id, day_of_year)
                         AS grp
                  FROM ({base_query}) orig_query) groups
            GROUP BY year, model_id, grp, match
            ORDER BY year, model_id
        """.format(base_query=base_query, condition=self.raw_condition)
        # First run the query and get a list of dicts with one result per sequence
        with connection.cursor() as cursor:
            cursor.execute(query, base_query_params)
            columns = [col[0] for col in cursor.description]
            sequences = (dict(zip(columns, row)) for row in cursor.fetchall())
        return sequences


class YearlyMaxConsecutiveDaysIndicator(DaysUnitsMixin, YearlySequenceIndicator):
    """ Abstract indicator to count the longest series of consecutive days on which a condition is
    met.

    The query is done with raw SQL, so the condition has to be a string that constitutes a
    valid condition when dropped into the WHEN clause inside the query.
    """

    def row_group_key(self, row):
        """ Key function for groupby to use to break input stream into chunks in indicators that
        require processing in code."""
        return tuple(row[key] for key in self.aggregate_keys)

    def aggregate(self):
        """
        Gets streaks of matching and non-matching days then picks the longest matching streak
        and returns its length, or zero if there are no matching streaks.
        """
        sequences = self.get_streaks()
        for key_vals, streaks in groupby(sequences, self.row_group_key):
            try:
                longest = max(seq['length'] for seq in streaks if seq['match'] == 1)
            except ValueError:
                longest = 0

            # Return an object with each of the keys and their values, along with the
            # aggregated value
            yield dict(zip(self.aggregate_keys, key_vals) + [('value', longest)])


class BasetempIndicatorMixin(object):
    """ Framework for pre-processing the basetemp parameter to a native unit
    """

    def __init__(self, *args, **kwargs):
        super(BasetempIndicatorMixin, self).__init__(*args, **kwargs)

        available_units = TemperatureConverter.available_units
        m = re.match(r'^(?P<value>-?\d+(\.\d+)?)(?P<unit>%s)?$' % '|'.join(available_units),
                     self.parameters['basetemp'])
        if not m:
            raise ValueError('Parameter basetemp must be numeric and optionally end with %s'
                             % str(available_units))

        value = float(m.group('value'))
        unit = m.group('unit')
        if unit is None:
            unit = self.parameters.get('units', self.default_units)

        converter = TemperatureConverter.get(unit, self.storage_units)
        self.parameters['basetemp'] = converter(value)
        self.parameters['units'] = self.storage_units
