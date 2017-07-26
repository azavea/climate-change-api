import inspect
import sys
from itertools import groupby
import numpy as np

from django.db.models import F, Sum, Avg, Max, Min
from django.conf import settings
from postgres_stats.aggregates import Percentile

from .abstract_indicators import (Indicator, ArrayIndicator, CountIndicator,
                                  BasetempIndicatorMixin, ArrayStreakIndicator,
                                  TemperatureThresholdIndicatorMixin,
                                  PrecipitationThresholdIndicatorMixin,
                                  YearlyMaxConsecutiveDaysIndicator,
                                  YearlySequenceIndicator)
from .params import (DegreeDayIndicatorParams, PercentileIndicatorParams, ExtremeIndicatorParams,
                     HeatWaveIndicatorParams)
from .unit_converters import (TemperatureUnitsMixin, PrecipUnitsMixin, DaysUnitsMixin,
                              CountUnitsMixin, TemperatureDeltaUnitsMixin, SECONDS_PER_DAY)


##########################
# Aggregated indicators

class MaxTemperatureThreshold(DaysUnitsMixin, TemperatureThresholdIndicatorMixin, CountIndicator):
    label = 'Max Temperature Threshold'
    description = ('Number of days where high temperature, generated from daily data ' +
                   'using all requested models, fulfils the comparison')
    variables = ('tasmax',)


class MinTemperatureThreshold(DaysUnitsMixin, TemperatureThresholdIndicatorMixin, CountIndicator):
    label = 'Min Temperature Threshold'
    description = ('Number of days where min temperature, generated from daily data ' +
                   'using all requested models, fulfils the comparison')
    variables = ('tasmin',)


class PrecipitationThreshold(DaysUnitsMixin, PrecipitationThresholdIndicatorMixin, CountIndicator):
    label = 'Precipitation Threshold'
    description = ('Number of days where precipitation, generated from daily data ' +
                   'using all requested models, fulfils the comparison')
    variables = ('pr',)


class AverageHighTemperature(TemperatureUnitsMixin, Indicator):
    label = 'Average High Temperature'
    description = ('Aggregated average high temperature, generated from daily data ' +
                   'using all requested models')
    variables = ('tasmax',)
    agg_function = Avg


class AverageHighTemperatureArray(ArrayIndicator, AverageHighTemperature):
    # Use the staticmethod decorated to prevent the function from being bound and  `self` from
    # being added as the first argument
    agg_function = staticmethod(np.mean)


class AverageLowTemperature(TemperatureUnitsMixin, Indicator):
    label = 'Average Low Temperature'
    description = ('Aggregated average low temperature, generated from daily data ' +
                   'using all requested models')
    variables = ('tasmin',)
    agg_function = Avg


class AverageLowTemperatureArray(ArrayIndicator, AverageLowTemperature):
    # Use the staticmethod decorated to prevent the function from being bound and  `self` from
    # being added as the first argument
    agg_function = staticmethod(np.mean)


class MaxHighTemperature(TemperatureUnitsMixin, Indicator):
    label = 'Maximum High Temperature'
    description = ('Maximum high temperature, generated from daily data ' +
                   'using all requested models')
    variables = ('tasmax',)
    agg_function = Max


class MaxHighTemperatureArray(ArrayIndicator, MaxHighTemperature):
    agg_function = max


class MinLowTemperature(TemperatureUnitsMixin, Indicator):
    label = 'Minimum Low Temperature'
    description = ('Minimum low temperature, generated from daily data ' +
                   'using all requested models')
    variables = ('tasmin',)
    agg_function = Min


class MinLowTemperatureArray(ArrayIndicator, MinLowTemperature):
    agg_function = min


class PercentileHighTemperature(TemperatureUnitsMixin, Indicator):
    label = 'Percentile High Temperature'
    description = ('The specified percentile of high temperature for each timespan. '
                   'Defaults to 50th percentile (Median)')
    variables = ('tasmax',)
    params_class = PercentileIndicatorParams
    params_class_kwargs = {'percentile': 50}

    def agg_function(self, expression):
        return Percentile(expression, int(self.params.percentile.value) / 100.0)


class PercentileHighTemperatureArray(ArrayIndicator, PercentileHighTemperature):
    def agg_function(self, values):
        percentile = self.params.percentile.value
        return np.percentile(values, percentile)


class PercentileLowTemperature(TemperatureUnitsMixin, Indicator):
    label = 'Percentile Low Temperature'
    description = ('The specified percentile of low temperature for each timespan. '
                   'Defaults to 50th percentile (Median)')
    variables = ('tasmin',)
    params_class = PercentileIndicatorParams
    params_class_kwargs = {'percentile': 50}

    def agg_function(self, expression):
        return Percentile(expression, int(self.params.percentile.value) / 100.0)


class PercentileLowTemperatureArray(ArrayIndicator, PercentileLowTemperature):
    def agg_function(self, values):
        percentile = self.params.percentile.value
        return np.percentile(values, percentile)


class TotalPrecipitation(PrecipUnitsMixin, Indicator):
    label = 'Total Precipitation'
    description = 'Total precipitation'
    variables = ('pr',)
    # Precipitation is stored per-second, and we want a total for all days in the aggregation,
    # so we need to multiple each day's value by 86400 to get the total for that day and then
    # sum the results
    expression = F('pr') * SECONDS_PER_DAY
    agg_function = Sum


class PercentilePrecipitation(PrecipUnitsMixin, Indicator):
    label = 'Percentile Precipitation'
    description = ('The specified percentile of precipitation for each timespan. '
                   'Defaults to 50th percentile (Median)')
    variables = ('pr',)
    params_class = PercentileIndicatorParams
    params_class_kwargs = {'percentile': 50}

    def agg_function(self, expression):
        return Percentile(expression, int(self.params.percentile.value) / 100.0) * SECONDS_PER_DAY


class PercentilePrecipitationArray(ArrayIndicator, PercentilePrecipitation):
    def agg_function(self, values):
        percentile = self.params.percentile.value
        return np.percentile(values, percentile) * SECONDS_PER_DAY


class FrostDays(DaysUnitsMixin, CountIndicator):
    label = 'Frost Days'
    description = ('Number of days per period in which the daily low temperature is ' +
                   'below the freezing point of water')
    variables = ('tasmin',)
    conditions = {'tasmin__lt': 273.15}


class YearlyMaxConsecutiveDryDays(YearlyMaxConsecutiveDaysIndicator):
    label = 'Yearly Max Consecutive Dry Days'
    description = ('Maximum number of consecutive days with no precipitation')
    variables = ('pr',)
    raw_condition = 'pr = 0'


class YearlyDrySpells(CountUnitsMixin, YearlySequenceIndicator):
    label = 'Yearly Dry Spells'
    description = ('Total number of times per period that there are 5 or more consecutive ' +
                   'days without precipitation')
    variables = ('pr',)
    raw_condition = 'pr = 0'

    def aggregate(self):
        """Call get_streaks to get all sequences of zero or non-zero precip.

        Then counts the zero-precip ones that are at least 5 days long.
        """
        sequences = self.get_streaks()
        for key_vals, streaks in groupby(sequences, self.row_group_key):
            num_dry_spells = sum(1 for seq in streaks if seq['match'] == 1 and seq['length'] >= 5)

            yield dict(list(zip(self.aggregate_keys, key_vals)) + [('value', num_dry_spells)])


class YearlyDrySpellsArray(ArrayStreakIndicator, YearlyDrySpells):
    predicate = staticmethod(lambda pr: pr == 0)
    min_streak = 5


class ExtremePrecipitationEvents(CountUnitsMixin, CountIndicator):
    label = 'Extreme Precipitation Events'
    description = ('Total number of times per period daily precipitation exceeds the specified '
                   'percentile of historic observations')
    params_class = ExtremeIndicatorParams
    params_class_kwargs = {'percentile': 99}
    variables = ('pr',)

    conditions = {'pr__gt': F('map_cell__baseline__pr')}

    @property
    def filters(self):
        return {'map_cell__baseline__historic_range__pk': int(self.params.historic_range.value),
                'map_cell__baseline__percentile': self.params.percentile.value}


class ExtremeHeatEvents(CountUnitsMixin, CountIndicator):
    label = 'Extreme Heat Events'
    description = ('Total number of times per period daily maximum temperature exceeds the '
                   'specified percentile of historic observations')
    params_class = ExtremeIndicatorParams
    params_class_kwargs = {'percentile': 99}
    variables = ('tasmax',)

    conditions = {'tasmax__gt': F('map_cell__baseline__tasmax')}

    @property
    def filters(self):
        return {'map_cell__baseline__historic_range__pk': int(self.params.historic_range.value),
                'map_cell__baseline__percentile': self.params.percentile.value}


class ExtremeColdEvents(CountUnitsMixin, CountIndicator):
    label = 'Extreme Cold Events'
    description = ('Total number of times per period daily minimum temperature is below the '
                   'specified percentile of historic observations')
    params_class = ExtremeIndicatorParams
    params_class_kwargs = {'percentile': 1}
    variables = ('tasmin',)

    conditions = {'tasmin__lt': F('map_cell__baseline__tasmin')}

    @property
    def filters(self):
        return {'map_cell__baseline__historic_range__pk': int(self.params.historic_range.value),
                'map_cell__baseline__percentile': self.params.percentile.value}


class DiurnalTemperatureRange(TemperatureDeltaUnitsMixin, Indicator):
    label = 'Diurnal Temperature Range'
    description = ('Average difference between daily max and daily min temperature')
    variables = ('tasmax', 'tasmin',)
    agg_function = Avg
    expression = (F('tasmax') - F('tasmin'))


class DiurnalTemperatureRangeArray(ArrayStreakIndicator, DiurnalTemperatureRange):
    def aggregate(self, bucket):
        pairs = zip(bucket['tasmax'], bucket['tasmin'])
        return np.mean([tasmax - tasmin for tasmax, tasmin in pairs])


class HeatingDegreeDays(TemperatureDeltaUnitsMixin, BasetempIndicatorMixin, Indicator):
    label = 'Heating Degree Days'
    description = 'Total difference of daily average temperature to a reference base temperature'
    variables = ('tasmax', 'tasmin',)
    agg_function = Sum
    params_class = DegreeDayIndicatorParams

    @property
    def conditions(self):
        # (A+B)/2 <= C translates to A <= 2C - B
        return {'tasmin__lte': (2 * self.params.basetemp.value) - F('tasmax')}

    @property
    def expression(self):
        return self.params.basetemp.value - (F('tasmax') + F('tasmin')) / 2


class HeatingDegreeDaysArray(ArrayIndicator, HeatingDegreeDays):
    def aggregate(self, bucket):
        pairs = zip(bucket['tasmax'], bucket['tasmin'])
        # Get the average temperature to compare with
        average_temp = ((tasmax + tasmin) / 2 for tasmax, tasmin in pairs)
        # Only count days that are below the threshold temperature
        heating_days = (temp for temp in average_temp if temp < self.params.basetemp.value)
        # Sum the difference for all days below the threshold
        return sum(self.params.basetemp.value - temp for temp in heating_days)


class CoolingDegreeDays(TemperatureDeltaUnitsMixin, BasetempIndicatorMixin, Indicator):
    label = 'Cooling Degree Days'
    description = 'Total difference of daily average temperature to a reference base temperature '
    variables = ('tasmax', 'tasmin',)
    agg_function = Sum
    params_class = DegreeDayIndicatorParams

    @property
    def conditions(self):
        # (A+B)/2 >= C translates to A >= 2C - B
        return {'tasmax__gte': (2 * self.params.basetemp.value) - F('tasmin')}

    @property
    def expression(self):
        return (F('tasmax') + F('tasmin')) / 2 - self.params.basetemp.value


class CoolingDegreeDaysArray(ArrayIndicator, CoolingDegreeDays):
    def aggregate(self, bucket):
        pairs = zip(bucket['tasmax'], bucket['tasmin'])
        # Get the average temperature to compare with
        average_temp = ((tasmax + tasmin) / 2 for tasmax, tasmin in pairs)
        # Only count days that are above the threshold temperature
        cooling_days = (temp for temp in average_temp if temp > self.params.basetemp.value)
        # Sum the difference for all days above the threshold
        return sum(temp - self.params.basetemp.value for temp in cooling_days)


class AccumulatedFreezingDegreeDays(TemperatureDeltaUnitsMixin, Indicator):
    label = 'Accumulated Freezing Degree Days'
    description = ('Maximum cumulative total of differences in average daily temperature and '
                   'freezing for consecutive days across the aggregation period.')
    variables = ('tasmax', 'tasmin')

    @property
    def expression(self):
        return 273.15 - (F('tasmax') + F('tasmin')) / 2

    def aggregate(self):
        # Loop over all data points in each aggregation period and track the maximum total
        self.queryset = (self.queryset.values(*self.aggregate_keys).annotate(value=self.expression)
                         .order_by('data_source__model', 'agg_key', 'data_source__year',
                                   'day_of_year'))

        for key_vals, days in groupby(self.queryset, self.row_group_key):
            total = 0
            max_total = 0
            for day in days:
                total += day['value']
                if total < 0:
                    # Total cannot go below 0
                    total = 0
                elif total > max_total:
                    max_total = total

            yield dict(list(zip(self.aggregate_keys, key_vals)) + [('value', max_total)])


class HeatWaveDurationIndex(YearlyMaxConsecutiveDaysIndicator):
    label = 'Heat Wave Duration Index'
    description = ('Maximum period of consecutive days with daily high temperature greater than '
                   '5C above historic norm')
    variables = ('tasmax',)
    raw_condition = 'tasmax > avg_tasmax + 5'
    params_class = HeatWaveIndicatorParams

    @property
    def filters(self):
        return {'day_of_year': F('map_cell__historic_average__day_of_year'),
                'map_cell__historic_average__historic_range__pk':
                    int(self.params.historic_range.value)}

    def aggregate(self):
        self.queryset = self.queryset.annotate(avg_tasmax=F('map_cell__historic_average__tasmax'))
        return super(HeatWaveDurationIndex, self).aggregate()


class HeatWaveIncidents(CountUnitsMixin, YearlySequenceIndicator):
    label = 'Heat Wave Incidents'
    description = ('Number of times daily high temperature exceeds 5C above historic norm for at '
                   'least 5 consecutive days')
    variables = ('tasmax',)
    raw_condition = 'tasmax > avg_tasmax + 5'
    params_class = HeatWaveIndicatorParams

    @property
    def filters(self):
        return {'day_of_year': F('map_cell__historic_average__day_of_year'),
                'map_cell__historic_average__historic_range__pk':
                    int(self.params.historic_range.value)}

    def aggregate(self):
        """Call get_streaks to get all sequences of abnormally hot days.

        Counts the number that are at least 5 days long.
        """
        self.queryset = self.queryset.annotate(avg_tasmax=F('map_cell__historic_average__tasmax'))
        sequences = self.get_streaks()
        for key_vals, streaks in groupby(sequences, self.row_group_key):
            num_dry_spells = sum(1 for seq in streaks if seq['match'] == 1 and seq['length'] >= 5)

            yield dict(list(zip(self.aggregate_keys, key_vals)) + [('value', num_dry_spells)])


def list_available_indicators():
    """List the defined class members of this module as the available indicators."""
    class_members = inspect.getmembers(sys.modules[__name__], inspect.isclass)
    indicators = [member[1] for member in class_members if member[1].__module__ == __name__ and
                  not member[1].__name__.endswith('Array')]
    return [i.to_dict() for i in indicators]


def indicator_factory(indicator_name):
    """Return a valid indicator class based on the string provided.

    Given a lower case, underscore separated indicator name, return the class associated
    with it. e.g. frost_days -> indicators.models.FrostDays
    If no match found, return None.
    """
    this_module = sys.modules[__name__]
    class_name = ''.join([s.capitalize() for s in indicator_name.split('_')])
    if settings.FEATURE_FLAGS['array_data'] and hasattr(this_module, '{}Array'.format(class_name)):
        # If the Array Data feature flag (FF) is set, automatically prefer [...]Array indicators
        class_name = '{}Array'.format(class_name)
    return getattr(this_module, class_name, None)
