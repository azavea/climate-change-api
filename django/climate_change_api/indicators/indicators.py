import inspect
import sys
from itertools import groupby
import numpy as np

from .abstract_indicators import (ArrayBaselineIndicator,
                                  ArrayHistoricAverageIndicator,
                                  ArrayIndicator,
                                  ArrayPredicateIndicator,
                                  ArrayStreakIndicator,
                                  ArrayThresholdIndicator,
                                  BasetempIndicatorMixin,
                                  PrecipitationThresholdIndicatorMixin,
                                  TemperatureThresholdIndicatorMixin)
from .params import (DegreeDayIndicatorParams,
                     ExtremeIndicatorParams,
                     HeatWaveIndicatorParams,
                     PercentileIndicatorParams)
from .unit_converters import (CountUnitsMixin,
                              DaysUnitsMixin,
                              PrecipUnitsMixin,
                              TemperatureDeltaUnitsMixin,
                              TemperatureUnitsMixin,
                              SECONDS_PER_DAY)
from .utils import running_total


##########################
# Aggregated indicators

class MaxTemperatureThreshold(DaysUnitsMixin,
                              TemperatureThresholdIndicatorMixin,
                              ArrayThresholdIndicator):
    label = 'Max Temperature Threshold'
    description = ('Number of days where high temperature, generated from daily data ' +
                   'using all requested models, fulfils the comparison')
    variables = ('tasmax',)


class MinTemperatureThreshold(DaysUnitsMixin,
                              TemperatureThresholdIndicatorMixin,
                              ArrayThresholdIndicator):
    label = 'Min Temperature Threshold'
    description = ('Number of days where min temperature, generated from daily data ' +
                   'using all requested models, fulfils the comparison')
    variables = ('tasmin',)


class PrecipitationThreshold(DaysUnitsMixin,
                             PrecipitationThresholdIndicatorMixin,
                             ArrayThresholdIndicator):
    label = 'Precipitation Threshold'
    description = ('Number of days where precipitation, generated from daily data ' +
                   'using all requested models, fulfils the comparison')
    variables = ('pr',)


class AverageHighTemperature(TemperatureUnitsMixin, ArrayIndicator):
    label = 'Average High Temperature'
    description = ('Aggregated average high temperature, generated from daily data ' +
                   'using all requested models')
    variables = ('tasmax',)
    # Use the staticmethod decorated to prevent the function from being bound and  `self` from
    # being added as the first argument
    agg_function = staticmethod(np.mean)


class AverageLowTemperature(TemperatureUnitsMixin, ArrayIndicator):
    label = 'Average Low Temperature'
    description = ('Aggregated average low temperature, generated from daily data ' +
                   'using all requested models')
    variables = ('tasmin',)
    # Use the staticmethod decorated to prevent the function from being bound and  `self` from
    # being added as the first argument
    agg_function = staticmethod(np.mean)


class MaxHighTemperature(TemperatureUnitsMixin, ArrayIndicator):
    label = 'Maximum High Temperature'
    description = ('Maximum high temperature, generated from daily data ' +
                   'using all requested models')
    variables = ('tasmax',)
    agg_function = max


class MinLowTemperature(TemperatureUnitsMixin, ArrayIndicator):
    label = 'Minimum Low Temperature'
    description = ('Minimum low temperature, generated from daily data ' +
                   'using all requested models')
    variables = ('tasmin',)
    agg_function = min


class PercentileHighTemperature(TemperatureUnitsMixin, ArrayIndicator):
    label = 'Percentile High Temperature'
    description = ('The specified percentile of high temperature for each timespan. '
                   'Defaults to 50th percentile (Median)')
    variables = ('tasmax',)
    params_class = PercentileIndicatorParams
    params_class_kwargs = {'percentile': 50}

    def agg_function(self, values):
        percentile = self.params.percentile.value
        return np.percentile(values, percentile)


class PercentileLowTemperature(TemperatureUnitsMixin, ArrayIndicator):
    label = 'Percentile Low Temperature'
    description = ('The specified percentile of low temperature for each timespan. '
                   'Defaults to 50th percentile (Median)')
    variables = ('tasmin',)
    params_class = PercentileIndicatorParams
    params_class_kwargs = {'percentile': 50}

    def agg_function(self, values):
        percentile = self.params.percentile.value
        return np.percentile(values, percentile)


class TotalPrecipitation(PrecipUnitsMixin, ArrayIndicator):
    label = 'Total Precipitation'
    description = 'Total precipitation'
    variables = ('pr',)

    @staticmethod
    def agg_function(values):
        """Convert precipitation rate to total amount.

        Precipitation is stored per-second, and we want a total for all days in the aggregation,
        so we need to multiply the value by 86400.
        """
        return sum(values) * SECONDS_PER_DAY


class PercentilePrecipitation(PrecipUnitsMixin, ArrayIndicator):
    label = 'Percentile Precipitation'
    description = ('The specified percentile of precipitation for each timespan. '
                   'Defaults to 50th percentile (Median)')
    variables = ('pr',)
    params_class = PercentileIndicatorParams
    params_class_kwargs = {'percentile': 50}

    def agg_function(self, values):
        percentile = self.params.percentile.value
        return np.percentile(values, percentile) * SECONDS_PER_DAY


class FrostDays(DaysUnitsMixin, ArrayIndicator):
    label = 'Frost Days'
    description = ('Number of days per period in which the daily low temperature is ' +
                   'below the freezing point of water')
    variables = ('tasmin',)

    @classmethod
    def agg_function(cls, bucket):
        comparator = (lambda a: a <= 273.15)
        count = sum(1 for value in bucket if comparator(value))
        return count


class MaxConsecutiveDryDays(DaysUnitsMixin, ArrayIndicator):
    label = 'Max Consecutive Dry Days'
    description = ('Maximum number of consecutive days with no precipitation')
    variables = ('pr',)

    @staticmethod
    def agg_function(precipitation):
        # Combine all days into groups of consective days based on if there is rain that day or not
        rain_groups = groupby(precipitation, lambda pr: pr > 0)
        # Filter out any groups of consecutive days with rain
        dry_periods = (days for has_rain, days in rain_groups if not has_rain)
        # Calculate the number of days without rain in each group
        dry_lengths = (sum(1 for pr in days) for days in dry_periods)
        # Return the biggest one
        try:
            return max(dry_lengths)
        except ValueError:
            # If every single day had rain, then the longest streak was 0
            return 0


class DrySpells(CountUnitsMixin, ArrayStreakIndicator):
    label = 'Dry Spells'
    description = ('Total number of times per period that there are 5 or more consecutive ' +
                   'days without precipitation')
    variables = ('pr',)
    predicate = staticmethod(lambda pr: pr == 0)
    min_streak = 5


class ExtremePrecipitationEvents(CountUnitsMixin, ArrayBaselineIndicator):
    label = 'Extreme Precipitation Events'
    description = ('Total number of times per period daily precipitation exceeds the specified '
                   'percentile of historic observations')
    params_class = ExtremeIndicatorParams
    params_class_kwargs = {'percentile': 99}
    variables = ('pr',)

    def agg_function(self, values):
        return sum(1 for v in values if self.baseline and v > self.baseline.pr)


class ExtremeHeatEvents(CountUnitsMixin, ArrayBaselineIndicator):
    label = 'Extreme Heat Events'
    description = ('Total number of times per period daily maximum temperature exceeds the '
                   'specified percentile of historic observations')
    params_class = ExtremeIndicatorParams
    params_class_kwargs = {'percentile': 99}
    variables = ('tasmax',)

    def agg_function(self, values):
        return sum(1 for v in values if self.baseline and v > self.baseline.tasmax)


class ExtremeColdEvents(CountUnitsMixin, ArrayBaselineIndicator):
    label = 'Extreme Cold Events'
    description = ('Total number of times per period daily minimum temperature is below the '
                   'specified percentile of historic observations')
    params_class = ExtremeIndicatorParams
    params_class_kwargs = {'percentile': 1}
    variables = ('tasmin',)

    def agg_function(self, values):
        return sum(1 for v in values if self.baseline and v < self.baseline.tasmin)


class DiurnalTemperatureRange(TemperatureDeltaUnitsMixin, ArrayStreakIndicator):
    label = 'Diurnal Temperature Range'
    description = ('Average difference between daily max and daily min temperature')
    variables = ('tasmax', 'tasmin',)

    def aggregate(self, daily_values):
        # daily_values is an iterator of tuples ordered in the same order as self.variables,
        # so for us each value is (tasmax_val, tasmin_val)
        return np.mean([tasmax - tasmin for tasmax, tasmin in daily_values])


class HeatingDegreeDays(TemperatureDeltaUnitsMixin,
                        BasetempIndicatorMixin,
                        ArrayIndicator):
    label = 'Heating Degree Days'
    description = 'Total difference of daily average temperature to a reference base temperature'
    variables = ('tasmax', 'tasmin',)
    agg_function = sum
    params_class = DegreeDayIndicatorParams

    def aggregate(self, daily_values):
        # daily_values is an iterator of tuples ordered in the same order as self.variables
        # Use that to get the day's average temperature to compare with
        average_temp = ((tasmax + tasmin) / 2 for tasmax, tasmin in daily_values)
        # Only count days that are below the threshold temperature
        heating_days = (temp for temp in average_temp if temp < self.params.basetemp.value)
        # Sum the difference for all days below the threshold
        return sum(self.params.basetemp.value - temp for temp in heating_days)


class CoolingDegreeDays(TemperatureDeltaUnitsMixin,
                        BasetempIndicatorMixin,
                        ArrayIndicator):
    label = 'Cooling Degree Days'
    description = 'Total difference of daily average temperature to a reference base temperature '
    variables = ('tasmax', 'tasmin',)
    agg_function = sum
    params_class = DegreeDayIndicatorParams

    def aggregate(self, daily_values):
        # daily_values is an iterator of tuples ordered in the same order as self.variables
        # Use that to get the day's average temperature to compare with
        average_temp = ((tasmax + tasmin) / 2 for tasmax, tasmin in daily_values)
        # Only count days that are above the threshold temperature
        cooling_days = (temp for temp in average_temp if temp > self.params.basetemp.value)
        # Sum the difference for all days above the threshold
        return sum(temp - self.params.basetemp.value for temp in cooling_days)


class AccumulatedFreezingDegreeDays(TemperatureDeltaUnitsMixin,
                                    ArrayIndicator):
    label = 'Accumulated Freezing Degree Days'
    description = ('Maximum cumulative total of differences in average daily temperature and '
                   'freezing for consecutive days across the aggregation period.')
    variables = ('tasmax', 'tasmin')

    def aggregate(self, daily_values):
        # daily_values is an iterator of tuples ordered in the same order as self.variables
        # Use that to get the day's average temperature to compare with
        average_temp = ((tasmax + tasmin) / 2 for tasmax, tasmin in daily_values)
        # Get the difference of the average from freezing
        freezing_degree_days = (273.15 - temp for temp in average_temp)

        # Convert each data point into a running total, bounded at 0
        accumulated_degree_days = running_total(freezing_degree_days, 0)

        try:
            # Return the peak running total for this period
            return max(accumulated_degree_days)
        except ValueError:
            # ....there were no days in this period? None?
            return 0


class HeatWaveDurationIndex(DaysUnitsMixin, ArrayPredicateIndicator, ArrayHistoricAverageIndicator):
    label = 'Heat Wave Duration Index'
    description = ('Maximum period of consecutive days with daily high temperature greater than '
                   '5C above historic norm')
    variables = ('tasmax', 'historical_tasmax')
    params_class = HeatWaveIndicatorParams
    agg_function = max

    @staticmethod
    def predicate(pair):
        """Determine if a day is abnormally warm enough to constitute part of a heatwave."""
        tasmax, historical = pair
        return tasmax > historical + 5


class HeatWaveIncidents(CountUnitsMixin,
                        ArrayStreakIndicator,
                        ArrayHistoricAverageIndicator):
    label = 'Heat Wave Incidents'
    description = ('Number of times daily high temperature exceeds 5C above historic norm for at '
                   'least 5 consecutive days')
    variables = ('tasmax', 'historical_tasmax')
    params_class = HeatWaveIndicatorParams
    min_streak = 5

    @staticmethod
    def predicate(pair):
        """Determine if a day is abnormally warm enough to constitute part of a heatwave."""
        tasmax, historical = pair
        return tasmax > historical + 5


def list_available_indicators():
    """List the defined class members of this module as the available indicators."""
    class_members = inspect.getmembers(sys.modules[__name__], inspect.isclass)
    indicators = [member[1] for member in class_members if member[1].__module__ == __name__]
    return [i.to_dict() for i in indicators]


def indicator_factory(indicator_name):
    """Return a valid indicator class based on the string provided.

    Given a lower case, underscore separated indicator name, return the class associated
    with it. e.g. frost_days -> indicators.indicators.FrostDays
    If no match found, return None.
    """
    this_module = sys.modules[__name__]
    class_name_parts = [s.capitalize() for s in indicator_name.split('_')]

    # Strip any Yearly prefix to maintain historical compatability, for example YearlyDrySpells
    if class_name_parts[0] == 'Yearly':
        class_name_parts = class_name_parts[1:]
    class_name = ''.join(class_name_parts)
    return getattr(this_module, class_name, None)
