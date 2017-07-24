from collections import OrderedDict, defaultdict
from itertools import groupby
import re

from django.db.models import F, Case, When, FloatField, Sum
from django.db import connection


from climate_data.models import ClimateData, ClimateDataYear, ClimateDataBaseline
from climate_data.filters import ClimateDataFilterSet
from .params import IndicatorParams, ThresholdIndicatorParams
from .serializers import IndicatorSerializer
from .unit_converters import DaysUnitsMixin, TemperatureConverter, PrecipitationConverter
from .partitioners import (YearlyPartitioner, MonthlyPartitioner, QuarterlyPartitioner,
                           OffsetYearlyPartitioner, CustomPartitioner)
from . import queryset_generator


class Indicator(object):

    label = ''
    description = ''
    valid_aggregations = ('yearly', 'quarterly', 'monthly', 'offset_yearly', 'custom')
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
    params_class_kwargs = {}

    # Subclasses should use a units mixin from 'unit_converters' to define these units
    # attributes and any necessary conversion functions
    storage_units = None
    default_units = None
    available_units = (None,)
    parameters = None

    # These are the keys that values are identified by when they come from the database.
    aggregate_keys = ['agg_key', 'data_source__model']

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
        """Return the instantiated IndicatorParams object for this class.

        Should not validate the IndicatorParams.
        """
        return cls.params_class(cls.default_units, cls.available_units, cls.valid_aggregations,
                                **cls.params_class_kwargs)

    @classmethod
    def name(cls):
        def convert(name):
            """Convert caps case string to snake case, e.g. IndicatorClass -> indicator_class."""
            s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
            return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
        return convert(cls.__name__)

    @classmethod
    def to_dict(cls):
        """Return a dict representation of the indicator."""
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
        """Get the initial indicator queryset.

        ClimateData initially filtered by city/scenario and optionally years/models as passed
        by the constructor.
        """
        # Get the queryset generator for this indicator's time aggregation
        generator = queryset_generator.get(self.params.time_aggregation.value)
        key_params = {}

        # The custom range config accepts a user-defined parameter to pick which dates to use
        if self.params.custom_time_agg.value is not None:
            key_params['custom_time_agg'] = self.params.custom_time_agg.value

        # Use the queryset generator classes to construct the initial base climate data queryset
        queryset = generator.create_queryset(
            years=self.params.years.value,
            models=self.params.models.value,
            scenario=self.scenario,
            key_params=key_params
        ).filter(
            map_cell=self.city.map_cell
        )

        if self.filters is not None:
            queryset = queryset.filter(**self.filters)

        return queryset

    @property
    def expression(self):
        return self.variables[0]

    def aggregate(self):
        """Calculate the indicator aggregation.

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
        """Convert aggregated results to the requested unit.

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
        """Take results as a series of datapoints and collate them by key.

        @param aggregations list-of-dicts returned by aggregate method
        @returns Dict of list of values, keyed by the queryset's agg_key column
        """
        results = defaultdict(list)
        for result in aggregations:
            results[result['agg_key']].append(result['value'])
        return results

    def calculate(self):
        aggregations = self.aggregate()
        aggregations = self.convert_units(aggregations)
        collations = self.collate_results(aggregations)
        return self.serializer.to_representation(collations,
                                                 aggregations=self.params.agg.value.split(','))

    def row_group_key(self, row):
        """Break input stream into chunks in indicators that require processing in code.

        For use in GROUP BY.
        """
        return tuple(row[key] for key in self.aggregate_keys)


class CountIndicator(Indicator):
    """Counts days on which a condition is met.

    Essentially a specialized version of the AggregationIndicator where all values count as 1
    if they match the conditions and 0 in all other cases.
    """

    agg_function = Sum
    expression = 1


class YearlySequenceIndicator(CountIndicator):
    """Abstract indicator to count series of consecutive days on which a condition is met.

    The query is done with raw SQL, so the condition has to be a string that constitutes a
    valid condition when dropped into the WHEN clause inside the query.
    """

    valid_aggregations = ('yearly',)

    def get_streaks(self):
        """Partition the data series by query into consecutive days by condition.

        Return all the streaks sorted by year and model.

        Start from the existing queryset with year/model/etc filters already applied.

        Return non-matching as well as matching sequences to guarantee that any year that matches
        the filter parameters and for which we have data will be represented in the results set.
        Filtering out non-matches inside the query would mean we get no results for years with no
        matches, making them indistinguishable from years that were filtered out or for which
        there is no data.
        """
        (base_query, base_query_params) = (self.queryset.select_related('data_source')
                                               .query.sql_with_params())
        query = """
            SELECT agg_key, model_id as data_source__model,
                   count(*) as length, match
            FROM (SELECT agg_key, model_id, day_of_year,
                         (CASE WHEN {condition} THEN 1 ELSE 0 END) as match,
                         ROW_NUMBER() OVER(ORDER BY agg_key, model_id, day_of_year) -
                         ROW_NUMBER() OVER(PARTITION BY CASE WHEN {condition} THEN 1 ELSE 0 END
                                           ORDER BY agg_key, model_id, day_of_year)
                         AS grp
                  FROM ({base_query}) orig_query) groups
            GROUP BY agg_key, model_id, grp, match
            ORDER BY agg_key, model_id
        """.format(base_query=base_query, condition=self.raw_condition)
        # First run the query and get a list of dicts with one result per sequence
        with connection.cursor() as cursor:
            cursor.execute(query, base_query_params)
            columns = [col[0] for col in cursor.description]
            sequences = (dict(zip(columns, row)) for row in cursor.fetchall())
        return sequences


class YearlyMaxConsecutiveDaysIndicator(DaysUnitsMixin, YearlySequenceIndicator):
    """Abstract indicator to count longest series of consecutive days on which a condition is met.

    The query is done with raw SQL, so the condition has to be a string that constitutes a
    valid condition when dropped into the WHEN clause inside the query.
    """

    def aggregate(self):
        """Get streaks of days by match then picks the longest matching streak.

        Return the streak length, or zero if there are no matching streaks.
        """
        sequences = self.get_streaks()
        for key_vals, streaks in groupby(sequences, self.row_group_key):
            try:
                longest = max(seq['length'] for seq in streaks if seq['match'] == 1)
            except ValueError:
                longest = 0

            # Return an object with each of the keys and their values, along with the
            # aggregated value
            yield dict(list(zip(self.aggregate_keys, key_vals)) + [('value', longest)])


class BasetempIndicatorMixin(object):
    """Framework for pre-processing the basetemp parameter to a native unit."""

    def __init__(self, *args, **kwargs):
        super(BasetempIndicatorMixin, self).__init__(*args, **kwargs)

        value = self.params.basetemp.value
        basetemp_units = self.params.basetemp_units.value
        unit = basetemp_units if basetemp_units is not None else self.params.units.value

        converter = TemperatureConverter.get(unit, self.storage_units)
        self.params.basetemp.value = converter(float(value))
        self.params.basetemp_units.value = self.storage_units


class ThresholdIndicatorMixin(object):
    """Framework for capturing and pre-processing threshold parameters."""

    params_class = ThresholdIndicatorParams

    def __init__(self, *args, **kwargs):
        super(ThresholdIndicatorMixin, self).__init__(*args, **kwargs)
        self.set_threshold_values()

    def set_threshold_values(self):
            # Convert threshold value to appropriate format
            value = self.params.threshold.value
            unit = self.params.threshold_units.value

            if self.variables[0] != 'pr':
                default_unit = 'K'
                converter_type = TemperatureConverter
            else:
                default_unit = 'kg/m^2'
                converter_type = PrecipitationConverter

            converter = converter_type.get(unit, default_unit)

            self.params.threshold.value = converter(float(value))
            self.params.threshold_units.value = default_unit

    @property
    def conditions(self):
        return {str(self.variables[0]) + '__' +
                str(self.params.threshold_comparator.value): float(self.params.threshold.value)}


class TemperatureThresholdIndicatorMixin(ThresholdIndicatorMixin):
    params_class_kwargs = {'threshold_units': TemperatureConverter.available_units}


class PrecipitationThresholdIndicatorMixin(ThresholdIndicatorMixin):
    params_class_kwargs = {'threshold_units': PrecipitationConverter.available_units}


class ArrayIndicator(Indicator):
    """Dynamically calculate specific values for a location across time.

    Indicators can be simple metrics such as hottest high temperature or average precipitation, or
    more complicated concepts like Accumulated Freezing Degree Days which approximates the amount
    of freezing an area would experience.

    These are calculated for an area across a timespan, using a custom aggregation level such as
    one data point per year, per quarter, or for every month ('yearly', 'monthly', and 'quarterly'
    aggregation respectively)

    This serves as the fundamental piece that indicators use to achieve their specific goals.
    """

    valid_aggregations = ('yearly', 'quarterly', 'monthly', 'offset_yearly', 'custom')

    # Function to use to calculate the value for a bucket
    # Takes a sequence of values as parameter. In some cases (like numpy methods) the staticmethod
    # decorator may be needed to prevent the function from being bound and `self` being added as the
    # first argument
    agg_function = None

    def get_queryset(self):
        """Get the initial indicator queryset.

        ClimateData initially filtered by city/scenario and optionally years/models as passed
        by the constructor.
        """
        queryset = ClimateDataYear.objects.filter(
            map_cell=self.city.map_cell,
            data_source__scenario=self.scenario
        )

        filter_params = {}
        if self.params.time_aggregation.value == 'offset_yearly':
            # The offset_yearly aggregation needs an extra year before each requested year, so tell
            # the filter to offset each points starting year
            filter_params['offset_end'] = True

        filterset = ClimateDataFilterSet(**filter_params)
        queryset = filterset.filter_years(queryset, 'years', self.params.years.value)
        queryset = filterset.filter_models(queryset, 'models', self.params.models.value)

        return queryset

    def align_buckets(self):
        """Group raw data into buckets corresponding to the time aggregation.

        By default data is accumulated in buckets that align with calendar years. For monthly,
        quarterly, and other aggregations, we'll want to re-align the buckets to match the output
        """
        partitioner_class = {
            'yearly': YearlyPartitioner,
            'monthly': MonthlyPartitioner,
            'quarterly': QuarterlyPartitioner,
            'offset_yearly': OffsetYearlyPartitioner,
            'custom': CustomPartitioner
        }[self.params.time_aggregation.value]

        partitioner_params = {}

        # The custom time aggregation allows a user-defined parameter to choose which dates to use
        if self.params.custom_time_agg.value is not None:
            partitioner_params['spans'] = self.params.custom_time_agg.value

        # The partitioner will take a filtered ClimateDataYear queryset and produce
        # a sequence of tuples of the format (agg_key, {var: [data], ...}), one for each
        # relevant timespan within the queryset.
        partitioner = partitioner_class(self.variables, **partitioner_params)
        return partitioner(self.queryset)

    def calculate_value(self, data):
        """Calculate the value for the indicator for a given bucket."""
        for agg_key, variable_data in data:
            # Compact out any Nones in the data that might have been added to keep partitions even
            values = {var: (v for v in data if v is not None)
                      for var, data in variable_data.items()}
            # Return a dictionary for compatability with existing Indicator logic
            # in convert_units() and collate_results()
            yield {
                'agg_key': agg_key,
                'value': self.aggregate(values)
            }

    def aggregate(self, bucket):
        """Process an aggregation-aligned bucket of raw data into a single value.

        For most indicators this can be done simply by taking the relevant variable's data and
        passing it to a mathematical function like max or np.percentile, but for more complicated
        indicators it may be necessary to overload this to define how to handle interactions
        between variables
        """
        variable = self.variables[0]
        values = list(bucket[variable])
        return self.agg_function(values)

    def calculate(self):
        # Parse yearly-aggregated data into other aggregations as needed
        data = self.align_buckets()
        # Process raw variable data into indicator values
        data = self.calculate_value(data)
        # Convert indicator values into the requested units
        data = self.convert_units(data)
        # Collect results with a common key into a dictionary of keyed groups
        results = self.collate_results(data)
        # Serialize the keyed groups using the requested sub-aggregations
        return self.serializer.to_representation(results,
                                                 aggregations=self.params.agg.value.split(','))


class ArrayThresholdIndicator(ArrayIndicator):
    """Calculate the number of days a variable criteria ("threshold") is met."""

    @classmethod
    def get_comparator(cls):
        """Helper method to translate an aliased string param to its mathematical operation."""
        options = {'lt': lambda a, b: a < b,
                   'lte': lambda a, b: a <= b,
                   'gt': lambda a, b: a > b,
                   'gte': lambda a, b: a >= b}
        return options[cls.params_class.threshold_comparator.value]

    @classmethod
    def agg_function(cls, bucket):
        """Count number of days the threshold is met."""
        count = 0
        comparator = cls.get_comparator()
        for value in bucket:
            if comparator(value, cls.params_class.threshold.value):
                count += 1
        return count


class ArrayStreakIndicator(ArrayIndicator):
    """Calculate the number of times a criteria is met in a number of consecutive days.

    Streaks can be configured both in what the criteria to be met is, as well as the number of
    consecutive days needed to be considered a streak.
    """

    @classmethod
    def predicate(cls, value):
        """Return true if the value matches the condition of a streak."""
        raise NotImplementedError()

    # How many consecutive days should the criteria be met to count as a streak
    min_streak = 1

    @classmethod
    def agg_function(cls, bucket):
        """Return number of times the predicate is met for at least min_streak consecutive days."""
        count = 0
        # Use groupby to automatically divide the bucket into matches or non-matches
        for match, group in groupby(bucket, cls.predicate):
            # groupby groups don't have a len, but we can use sum to count how many items it has
            if match and sum(1 for v in group) >= cls.min_streak:
                count += 1
        return count


class ArrayBaselineIndicator(ArrayIndicator):
    def calculate_value(self, *args, **kwargs):
        self.baseline = ClimateDataBaseline.objects.get(
            map_cell=self.city.map_cell,
            historic_range_id=self.params.historic_range.value,
            percentile=self.params.percentile.value
        )

        return super(ArrayBaselineIndicator, self).calculate_value(*args, **kwargs)
