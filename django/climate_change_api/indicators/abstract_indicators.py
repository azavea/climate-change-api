from collections import OrderedDict, defaultdict
from itertools import groupby
import re
from datetime import date, timedelta

from django.db.models import F, Case, When, FloatField, Sum
from django.db import connection


from climate_data.models import ClimateData
from climate_data.filters import ClimateDataFilterSet
from .params import IndicatorParams
from .serializers import IndicatorSerializer
from .unit_converters import DaysUnitsMixin, TemperatureConverter
from .query_ranges import MonthRangeConfig, QuarterRangeConfig, CustomRangeConfig


class Indicator(object):

    label = ''
    description = ''
    valid_aggregations = ('yearly', 'quarterly', 'monthly', 'daily', 'custom')
    variables = ClimateData.VARIABLE_CHOICES

    # Filters define which rows match our query, conditions limit which rows
    # within that set fit the criteria. That is, if a filter excludes a row it is
    # completely ignored, but if a condition excludes a row it is replaced with
    # default_value.
    # This enables us to provide a value for timespans that have no matching
    # periods, but is imperfect and only works for aggregations where a default
    # value makes sense.
    filters = None
    conditions = None
    default_value = 0

    # The aggregation function defines how we should coalesce multiple data points
    # from the same aggregation (Values within the same scenario, time span and model -
    # note that per-model values are coalesced separately during serialization).
    # For example Sum, Count, Avg, etc.
    agg_function = F

    serializer_class = IndicatorSerializer
    params_class = IndicatorParams

    # Subclasses should use a units mixin from 'unit_converters' to define these units
    # attributes and any necessary conversion functions
    storage_units = None
    default_units = None
    available_units = (None,)
    parameters = None

    def __init__(self, city, scenario, parameters=None):
        if not city:
            raise ValueError('Indicator constructor requires a city instance')
        if not scenario:
            raise ValueError('Indicator constructor requires a scenario instance')

        self.city = city
        self.scenario = scenario

        self.params = self.init_params_class()
        self.params.validate(parameters)

        self.queryset = self.get_queryset()

        self.serializer = self.serializer_class()

    @classmethod
    def init_params_class(cls):
        """ Return the instantiated IndicatorParams object for this class

        Should not validate the IndicatorParams

        """
        return cls.params_class(cls.default_units, cls.available_units, cls.valid_aggregations)

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
            ('valid_aggregations', cls.valid_aggregations),
            ('variables', cls.variables),
            ('available_units', cls.available_units),
            ('default_units', cls.default_units),
            ('parameters', cls.init_params_class().to_dict()),
        ])

    def get_queryset(self):
        """ Get the initial indicator queryset

        ClimateData initially filtered by city/scenario and optionally years/models as passed
        by the constructor

        """
        filter_set = ClimateDataFilterSet()
        queryset = (ClimateData.objects.filter(map_cell=self.city.map_cell)
                    .filter(data_source__scenario=self.scenario))
        queryset = filter_set.filter_years(queryset, self.params.years.value)
        queryset = filter_set.filter_models(queryset, self.params.models.value)

        if self.filters is not None:
            queryset = queryset.filter(**self.filters)

        # For certain time aggregations, add a field to track which interval a data point is in
        interval_configs = {
            'monthly': MonthRangeConfig,
            'quarterly': QuarterRangeConfig,
            'custom': CustomRangeConfig
        }
        if self.params.time_aggregation.value in interval_configs:
            config = interval_configs[self.params.time_aggregation.value]
            params = {}

            # The custom range config accepts a user-defined parameter to pick which dates to use
            if self.params.intervals.value is not None:
                params['intervals'] = self.params.intervals.value

            queryset = (queryset
                        .annotate(interval=config.cases(**params))
                        .filter(interval__isnull=False))

        return queryset

    @property
    def aggregate_keys(self):
        return {
            'daily': ['data_source__year', 'day_of_year', 'data_source__model'],
            'monthly': ['data_source__year', 'interval', 'data_source__model'],
            'quarterly': ['data_source__year', 'interval', 'data_source__model'],
            'custom': ['data_source__year', 'interval', 'data_source__model'],
            'yearly': ['data_source__year', 'data_source__model']
        }.get(self.params.time_aggregation.value)

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
                 to `self.params.units.value`
        """
        converter = self.getConverter(self.storage_units, self.params.units.value)
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
        if self.params.time_aggregation.value == 'yearly':
            return year

        if self.params.time_aggregation.value == 'daily':
            day_of_year = result['day_of_year']
            day = date(year, 1, 1) + timedelta(days=day_of_year-1)
            return day.isoformat()

        template = {
            'monthly': '{year}-{int:02d}',
            'quarterly': '{year}-Q{int:0d}',
            'custom': '{year}-{int:02d}'
        }.get(self.params.time_aggregation.value)
        return template.format(year=year, int=(result['interval']+1))

    def calculate(self):
        aggregations = self.aggregate()
        aggregations = self.convert_units(aggregations)
        collations = self.collate_results(aggregations)
        return self.serializer.to_representation(collations,
                                                 aggregations=self.params.agg.value.split(','))


class CountIndicator(Indicator):
    """ Class to count days on which a condition is met.

    Essentially a specialized version of the AggregationIndicator where all values count as 1
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

    def row_group_key(self, row):
        """ Key function for groupby to use to break input stream into chunks in indicators that
        require processing in code."""
        return tuple(row[key] for key in self.aggregate_keys)

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

        value = self.params.basetemp.value
        basetemp_units = self.params.basetemp_units.value
        unit = basetemp_units if basetemp_units is not None else self.params.units.value

        converter = TemperatureConverter.get(unit, self.storage_units)
        self.params.basetemp.value = converter(float(value))
        self.params.basetemp_units.value = self.storage_units
