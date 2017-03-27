from collections import OrderedDict, defaultdict
from itertools import groupby
import re

from django.db.models import F, Case, When, FloatField, Sum
from django.db import connection


from climate_data.models import ClimateData
from .params import IndicatorParams, ThresholdIndicatorParams
from .serializers import IndicatorSerializer
from .unit_converters import DaysUnitsMixin, TemperatureConverter, PrecipitationConverter
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

    def row_group_key(self, row):
        """Break input stream into chunks in indicators that require processing in code.

        For use in GROUP BY.
        """
        return tuple(row[key] for key in self.aggregate_keys)

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
            sequences = (dict(list(zip(columns, row))) for row in cursor.fetchall())
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
