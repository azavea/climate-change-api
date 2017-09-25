from collections import OrderedDict, defaultdict
from itertools import groupby, chain
import logging
import re

from django.core.exceptions import ValidationError

from climate_data.models import (ClimateDataBaseline,
                                 ClimateDataYear,
                                 HistoricAverageClimateDataYear,
                                 ClimateDataset,
                                 ClimateDataCell)
from climate_data.filters import ClimateDataFilterSet
from .params import IndicatorParams, ThresholdIndicatorParams
from .serializers import IndicatorSerializer
from .unit_converters import (PrecipitationRateConverter,
                              TemperatureConverter)
from .partitioners import (CustomPartitioner,
                           MonthlyPartitioner,
                           OffsetYearlyPartitioner,
                           QuarterlyPartitioner,
                           YearlyPartitioner)
from .utils import merge_dicts

logger = logging.getLogger(__name__)

HISTORICAL_VARIABLE_PREFIX = 'historical_'


class Indicator(object):
    """Dynamically calculate specific values for a location across time.

    Indicators can be simple metrics such as hottest high temperature or average precipitation, or
    more complicated concepts like Accumulated Freezing Degree Days which approximates the amount
    of freezing an area would experience.

    These are calculated for an area across a timespan, using a custom aggregation level such as
    one data point per year, per quarter, or for every month ('yearly', 'monthly', and 'quarterly'
    aggregation respectively)

    This serves as the fundamental piece that indicators use to achieve their specific goals.
    """

    label = ''
    description = ''
    valid_aggregations = ('yearly', 'quarterly', 'monthly', 'offset_yearly', 'custom')
    variables = ClimateDataYear.VARIABLE_CHOICES

    # Dictionary storing custom parameters to pass to self.queryset.filter()
    filters = None

    # Function to use to calculate the value for a bucket
    # Takes a sequence of values as parameter. In some cases (like numpy methods) the staticmethod
    # decorator may be needed to prevent the function from being bound and `self` being added as the
    # first argument
    agg_function = None

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

        self.params = self.init_params_class()
        self.params.set_parameters(parameters)

        self.city = city
        self.scenario = scenario
        self.dataset = ClimateDataset.objects.get(name=self.params.dataset.value)

        found = (self.dataset.models.filter(name__in=self.params.models.value)
                                    .values_list('name', flat=True))
        invalid_models = set(self.params.models.value) - set(found)

        if invalid_models:
            raise ValidationError('Dataset %s has no data for model(s) %s'
                                  % (self.dataset.name, ','.join(invalid_models)))

        try:
            self.map_cell = self.city.get_map_cell(self.dataset)
        except ClimateDataCell.DoesNotExist:
            raise ValidationError('No data available for %s dataset at this location'
                                  % (self.dataset.name))

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
        queryset = ClimateDataYear.objects.filter(
            map_cell=self.map_cell,
            data_source__scenario=self.scenario,
            data_source__dataset=self.dataset
        )

        filter_params = {}
        if self.params.time_aggregation.value == 'offset_yearly':
            # The offset_yearly aggregation needs an extra year before each requested year, so tell
            # the filter to offset each points starting year
            filter_params['offset_end'] = True

        filterset = ClimateDataFilterSet(**filter_params)
        queryset = filterset.filter_years(queryset, 'years', ','.join(self.params.years.value))
        queryset = filterset.filter_models(queryset, 'models', ','.join(self.params.models.value))

        value_columns = ['data_source__year', 'data_source__model_id']
        value_columns.extend(var for var in self.variables
                             if not var.startswith(HISTORICAL_VARIABLE_PREFIX))
        queryset = queryset.values(*value_columns)

        return queryset

    def aggregate(self, daily_values):
        """Process an aggregation-aligned bucket of raw data into a single value.

        For most indicators this can be done simply by taking the relevant variable's data and
        passing it to a mathematical function like max or np.percentile, but for more complicated
        indicators it may be necessary to overload this to define how to handle interactions
        between variables
        """
        # numpy methods don't handle generators, so convert daily_values into a list just in case
        values_list = list(daily_values)
        return self.agg_function(values_list)

    def calculate(self):
        """Produce a dictionary of calculated numeric values in a list keyed by time aggregation.

        Uses a sequence of steps that each use an iterator of tuples of the form (agg_key, payload).
        Each step performs some transformation of the data, until we collate the iterator into a
        single dictionary for representation to the user.
        """
        # Load and partition data into a series of tuples of the form (agg_key, raw_values)
        data = self.generate_partitions()
        # Process the tuple's raw values into a single calculated value defined by the indicator
        data = self.calculate_value(data)
        # Localize indicator output values into the requested units, if necessary
        data = self.convert_units(data)

        # Convert the sequence of tuples into a dictionary, collecting all values with a given
        # aggregation key in a common list
        results = self.collate_results(data)

        # Serialize the keyed groups using the requested sub-aggregations
        return self.serializer.to_representation(results,
                                                 aggregations=self.params.agg.value)

    def calculate_value(self, data):
        """Calculate the value for the indicator for a given bucket."""
        for agg_key, variable_data in data:
            # If we have more than one variable, combine the variable data into daily values
            # This will be more useful for the indicators, and lets us filter unwanted data
            # (For instance, missing Leap Year days) without affecting day-to-day matching
            if len(self.variables) > 1:
                variable_sequences = (variable_data[var] for var in self.variables)
                paired_data = zip(*variable_sequences)
                # Filter out any daily values that have a None data point
                daily_values = (v for v in paired_data if all(val is not None for val in v))
            else:
                # Take the variable's data and convert it into a simple list, with no `None`s
                variable = self.variables[0]
                daily_values = (v for v in variable_data[variable] if v is not None)

            # Yield a single value calculated from the raw data by the indicator's aggregate()
            yield (agg_key, self.aggregate(daily_values))

    def collate_results(self, aggregations):
        """Take results as a series of datapoints and collate them by key.

        @param aggregations iterator of tuples containing aggregation key and indicator values
        @returns Dict of list of values, keyed by the tuple's first aggregation key value
        """
        results = defaultdict(list)
        for agg_key, value in aggregations:
            results[agg_key].append(value)
        return results

    def convert_units(self, aggregations):
        """Convert aggregated results to the requested unit.

        @param aggregations iterator of tuples containing aggregation keys and indicator values
        @returns Tuples in same format as the aggregations parameter, with values converted
                 to `self.params.units.value`
        """
        converter = self.getConverter(self.storage_units, self.params.units.value)
        for agg_key, value in aggregations:
            if value is not None:
                value = converter(value)
            yield (agg_key, value)

    def generate_model_segments(self):
        """Return a sequence of tuple iterators form (year, data) from a queryset result set.

        Each segment within the sequence shares a single data source model, to prevent
        partioning from accidentally slicing between models.
        """
        queryset = self.queryset.order_by('data_source__model_id', 'data_source__year')
        for model, yearly_data in groupby(queryset, lambda r: r.pop('data_source__model_id')):
            yield ((row.pop('data_source__year'), row) for row in yearly_data)

    def generate_partitions(self):
        """Group raw data into buckets corresponding to the time aggregation.

        By default data within a segment is in chunks that align with calendar years. For monthly,
        quarterly, and other aggregations, we'll want to re-align the chunks to match the output
        """
        # Split data into segments according to model, so the partitioner doesn't need to worry
        # about combining values between different prediction models
        model_segments = self.generate_model_segments()

        # Partition each segment individually, so there's no risk of accidentally connecting data
        # from unconnected data sources
        partitioner = self.get_partitioner()
        partitioned_segments = (partitioner(yearly_data) for yearly_data in model_segments)

        # Merge all of the segments into a string of tuples, all of the form (agg_key, payload)
        return chain.from_iterable(partitioned_segments)

    def get_partitioner(self):
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
            # TODO: #600, 601 - Remove this check once it can be handled in the params
            #                   validation framework
            if self.params.time_aggregation.value != 'custom':
                raise ValidationError('If custom_time_agg is provided, ' +
                                      'param time_aggregation must equal "custom"')
            partitioner_params['spans'] = self.params.custom_time_agg.value

        # The partitioner will take an iterator of (key, values) tuples, and produce a sequence of
        # tuples of the same format, with values resized to match the desired time aggregation
        return partitioner_class(**partitioner_params)


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
        self._set_threshold_values()

    def _set_threshold_values(self):
        # Convert threshold value / unit param to the units of the db values
        value = self.params.threshold.value
        unit = self.params.threshold_units.value

        if self.variables[0] != 'pr':
            db_storage_unit = 'K'
            converter_type = TemperatureConverter
        else:
            db_storage_unit = 'kg/m^2/s'
            converter_type = PrecipitationRateConverter

        converter = converter_type.get(unit, db_storage_unit)

        self.params.threshold.value = converter(float(value))
        self.params.threshold_units.value = db_storage_unit


class TemperatureThresholdIndicatorMixin(ThresholdIndicatorMixin):
    params_class_kwargs = {'threshold_units': TemperatureConverter.available_units}


class PrecipitationThresholdIndicatorMixin(ThresholdIndicatorMixin):
    params_class_kwargs = {'threshold_units': PrecipitationRateConverter.available_units}


class ArrayIndicator(Indicator):
    pass


class ArrayPredicateIndicator(ArrayIndicator):
    """Calculate a value based on if a criteria is met in groups of consecutive days."""

    @classmethod
    def predicate(cls, value):
        """Return true if the value matches the condition of a streak."""
        raise NotImplementedError()

    @classmethod
    def agg_function(cls, lengths):
        """Calculate a value based on a sequence of streak lengths.

        By default returns the number of days that matched the predicate.
        """
        return sum(l for l in lengths)

    def aggregate(self, daily_values):
        """Return number of times the predicate is met for at least min_streak consecutive days."""
        # Use groupby to automatically divide the bucket into matches or non-matches
        streak_groups = groupby(daily_values, self.predicate)
        # Filter out all non-matching groups
        matching_streaks = (values for matching, values in streak_groups if matching)
        # Calculate the length of every matching group
        streak_lengths = (sum(1 for v in values) for values in matching_streaks)

        try:
            # Pass the lengths sequence to the aggregation function to reduce to a single value
            return self.agg_function(streak_lengths)
        except ValueError:
            return 0


class ArrayThresholdIndicator(ArrayPredicateIndicator):
    """Calculate the number of days a variable criteria ("threshold") is met."""

    predicate = None

    def get_comparator(self):
        """Translate an aliased string param to its mathematical operation with a helper."""
        threshold = self.params_class.threshold.value
        options = {'lt': lambda val: val < threshold,
                   'lte': lambda val: val <= threshold,
                   'gt': lambda val: val > threshold,
                   'gte': lambda val: val >= threshold}
        return options[self.params_class.threshold_comparator.value]

    def aggregate(self, daily_values):
        # Compute comparator only just before we need it, so that we avoid initialization order
        # bugs that can occur if the adjusted threshold params values aren't ready in the __init__
        # chain.
        self.predicate = self.get_comparator()
        return super(ArrayThresholdIndicator, self).aggregate(daily_values)


class ArrayStreakIndicator(ArrayPredicateIndicator):
    """Calculate the number of times a predicate is met in a minimum number of consecutive days."""

    # How many consecutive days should the criteria be met to count as a streak
    min_streak = 1

    @classmethod
    def agg_function(cls, lengths):
        """Calculate the number of times a sequence is longer than min_streak."""
        return sum(1 for l in lengths if l >= cls.min_streak)


class ArrayBaselineIndicator(ArrayIndicator):
    def calculate_value(self, *args, **kwargs):
        try:
            self.baseline = ClimateDataBaseline.objects.get(
                map_cell=self.map_cell,
                historic_range_id=self.params.historic_range.value,
                percentile=self.params.percentile.value
            )
        except ClimateDataBaseline.DoesNotExist:
            logger.warning("No ClimateDataBaseline for " +
                           "<map_cell: {}, historic_range: {}, percentile: {}>"
                           .format(self.map_cell,
                                   self.params.historic_range.value,
                                   self.params.percentile.value))
            self.baseline = None

        return super(ArrayBaselineIndicator, self).calculate_value(*args, **kwargs)


class ArrayHistoricAverageIndicator(ArrayIndicator):
    def get_historical_averages(self):
        """Return a dictionary of historic values, keyed to use the historical_ prefix."""
        # Only load historical averages for the historical columns
        variables = [var for var in self.variables
                     if var.startswith(HISTORICAL_VARIABLE_PREFIX)]

        # Remove the prefix to get the raw database column names
        raw_variables = [var[len(HISTORICAL_VARIABLE_PREFIX):] for var in variables]

        # Load historical averages for our desired variables
        try:
            averages = (HistoricAverageClimateDataYear.objects.values(*raw_variables)
                        .get(map_cell=self.map_cell,
                             historic_range=self.params.historic_range.value))

            # Label the dictionary keys so they don't conflict with yearly data
            return {label: averages[var]
                    for label, var in zip(variables, raw_variables)}
        except HistoricAverageClimateDataYear.DoesNotExist:
            logger.warning("No HistoricAverageClimateDataYear for " +
                           "<map_cell: {}, historic_range: {}>"
                           .format(self.map_cell, self.params.historic_range.value))
            return {}

    def generate_model_segments(self):
        """Inject historical yearly values into every year's data payload as if they were native.

        This allows the partitioner to resize the chunks as needed, without needing to know too many
        details or have esoteric database logic built-in.
        """
        def append_historical_values(it, addenda):
            """Insert the addenda dictionary to every tuple's payload in the iterator."""
            for year, data in it:
                yield (year, merge_dicts(data, addenda))

        # Load daily averages, with remapped keys
        averages = self.get_historical_averages()

        # Get the segments of yearly data we want to inject our historical averages into
        segments = super(ArrayHistoricAverageIndicator, self).generate_model_segments()
        # Pass them through, but with our historic averages added
        for segment in segments:
            yield append_historical_values(segment, averages)
