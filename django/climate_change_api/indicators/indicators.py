import inspect
import sys
from itertools import groupby

from django.db.models import F, Avg, Max, Min

from .abstract_indicators import (YearlyAggregationIndicator, YearlyCountIndicator,
                                  YearlyMaxConsecutiveDaysIndicator,
                                  MonthlyAggregationIndicator, MonthlyCountIndicator,
                                  DailyRawIndicator)
from .unit_converters import (TemperatureUnitsMixin, PrecipUnitsMixin,
                              DaysUnitsMixin, CountUnitsMixin)


##########################
# Yearly indicators

class YearlyAverageHighTemperature(TemperatureUnitsMixin, YearlyAggregationIndicator):
    label = 'Yearly Average High Temperature'
    description = ('Aggregated yearly average high temperature, generated from daily data ' +
                   'using all requested models')
    variables = ('tasmax',)
    agg_function = Avg


class YearlyAverageLowTemperature(TemperatureUnitsMixin, YearlyAggregationIndicator):
    label = 'Yearly Average Low Temperature'
    description = ('Aggregated yearly average low temperature, generated from daily data ' +
                   'using all requested models')
    variables = ('tasmin',)
    agg_function = Avg


class YearlyMaxHighTemperature(TemperatureUnitsMixin, YearlyAggregationIndicator):
    label = 'Yearly Maximum High Temperature'
    description = ('Yearly maximum high temperature, generated from daily data ' +
                   'using all requested models')
    variables = ('tasmax',)
    agg_function = Max


class YearlyMinLowTemperature(TemperatureUnitsMixin, YearlyAggregationIndicator):
    label = 'Yearly Minimum Low Temperature'
    description = ('Yearly minimum low temperature, generated from daily data ' +
                   'using all requested models')
    variables = ('tasmin',)
    agg_function = Min


class YearlyTotalPrecipitation(PrecipUnitsMixin, YearlyAggregationIndicator):
    label = 'Yearly Total Precipitation'
    description = 'Yearly total precipitation'
    variables = ('pr',)
    agg_function = Avg
    default_units = 'in/year'


class YearlyFrostDays(DaysUnitsMixin, YearlyCountIndicator):
    label = 'Yearly Frost Days'
    description = ('Number of days per year in which the daily low temperature is ' +
                   'below the freezing point of water')
    variables = ('tasmin',)
    conditions = {'tasmin__lt': 273.15}


class YearlyMaxConsecutiveDryDays(YearlyMaxConsecutiveDaysIndicator):
    label = 'Yearly Max Consecutive Dry Days'
    description = ('Maximum number of consecutive days with no precipitation per year')
    variables = ('pr',)
    raw_condition = 'pr = 0'


class YearlyDrySpells(CountUnitsMixin, YearlyCountIndicator):
    label = 'Yearly Dry Spells'
    description = ('Total number of times per year that there are 5 or more consecutive ' +
                   'days without precipitation')
    variables = ('pr',)

    def aggregate(self):
        """ Since filtering for precip in the query means we get no data for a year/model if
        there were zero dry days, this pulls all relevant data and does the filtering and
        counting in code.
        """
        days = (self.queryset.order_by('data_source__year', 'data_source__model', 'day_of_year')
                             .values('data_source__year', 'data_source__model', 'day_of_year', 'pr')
                )
        # Loop through the results and add up dry spells by year and model
        counts = {}
        for day in days:
            year = counts.setdefault(day['data_source__year'], {})
            model = year.setdefault(day['data_source__model'], {'dry_days': 0,
                                                                'streaks': 0})
            if day['pr'] > 0:
                model['dry_days'] = 0
            else:
                model['dry_days'] += 1
            if model['dry_days'] == 5:
                model['streaks'] += 1
        # Convert the answers to the required return format
        results = [{'data_source__year': yr, 'data_source__model': md, 'value': value['streaks']}
                   for yr in counts for (md, value) in counts[yr].items()]
        return results


class YearlyExtremePrecipitationEvents(CountUnitsMixin, YearlyCountIndicator):
    label = 'Yearly Extreme Precipitation Events'
    description = ('Total number of times per year daily precipitation exceeds the 99th '
                   'percentile of observations from 1960 to 1995')
    variables = ('pr',)
    conditions = {'pr__gt': F('map_cell__baseline__precip_99p')}


class HeatWaveDurationIndex(CountUnitsMixin, YearlyCountIndicator):
    label = 'Heat Wave Duration Index'
    description = ('Maximum period of consecutive days with daily high temperature greater than '
                   '5C above historic norm')
    variables = ('tasmax',)

    def consecutive_value_lengths(self, sequence):
        # Group the values by their offset from an enumeration
        # Consecutive values will all have the same offset, any gaps will change it.
        for group, values in groupby(enumerate(sequence), lambda (i, v): i - v):
            # groupby() gives an iterator - but not a list - so we can't directly len() it
            # Rather than pass over the iterator just to convert it to a list so we can then count
            #  the elements we already processed, let's just count them directly.
            yield sum(1 for v in values)
        else:
            # There are no values in the list, so the longest consecutive series is 0
            yield 0

    def aggregate(self):
        """ Get all tasmax data for all of the years requested, then in memory process them to find
        consecutive days that exceed their historic average. We need to do this in Python rather in
        SQL because some places like Honolulu have absurdly consistent temperates and can go years
        without a single day significantly above average.
        """
        days = (self.queryset.order_by('data_source__year', 'data_source__model', 'day_of_year')
                             .values('data_source__year', 'data_source__model', 'day_of_year',
                                     'tasmax', 'map_cell__historic_average__tasmax')
                )

        # Read in all of the data grouped by year and model, so we can process each chunk as it
        #  comes in to find the longest sequence of consecutive dates
        # groupby() splits the sets by model and year, so we don't have to worry about tracking
        #  the changeover ourselves
        for model_year, days in groupby(days, self.row_group_key):
            (model, year) = model_year
            exceeding_days = (row['day_of_year'] for row in days
                              if row['tasmax'] > row['map_cell__historic_average__tasmax'] + 5)
            consecutive_counts = self.consecutive_value_lengths(exceeding_days)

            yield {'data_source__year': year,
                   'data_source__model': model,
                   'value': max(consecutive_counts)}


##########################
# Monthly indicators

class MonthlyAverageHighTemperature(TemperatureUnitsMixin, MonthlyAggregationIndicator):
    label = 'Monthly Average High Temperature'
    description = ('Aggregated monthly average high temperature, generated from daily data ' +
                   'using all requested models')
    variables = ('tasmax',)
    agg_function = Avg


class MonthlyAverageLowTemperature(TemperatureUnitsMixin, MonthlyAggregationIndicator):
    label = 'Monthly Average Low Temperature'
    description = ('Aggregated monthly average low temperature, generated from daily data ' +
                   'using all requested models')
    variables = ('tasmin',)
    agg_function = Avg


class MonthlyMaxHighTemperature(TemperatureUnitsMixin, MonthlyAggregationIndicator):
    label = 'Monthly Maximum High Temperature'
    description = ('Monthly maximum high temperature, generated from daily data ' +
                   'using all requested models')
    variables = ('tasmax',)
    agg_function = Max


class MonthlyMinLowTemperature(TemperatureUnitsMixin, MonthlyAggregationIndicator):
    label = 'Monthly Minimum Low Temperature'
    description = ('Monthly minimum low temperature, generated from daily data ' +
                   'using all requested models')
    variables = ('tasmin',)
    agg_function = Min


class MonthlyTotalPrecipitation(PrecipUnitsMixin, MonthlyAggregationIndicator):
    label = 'Monthly Total Precipitation'
    description = 'Monthly total precipitation'
    variables = ('pr',)
    agg_function = Avg


class MonthlyFrostDays(DaysUnitsMixin, MonthlyCountIndicator):
    label = 'Monthly Frost Days'
    description = ('Number of days per month in which the daily low temperature is ' +
                   'below the freezing point of water')
    variables = ('tasmin',)
    conditions = {'tasmin__lt': 273.15}


class MonthlyExtremePrecipitationEvents(CountUnitsMixin, MonthlyCountIndicator):
    label = 'Monthly Extreme Precipitation Events'
    description = ('Total number of times per month daily precipitation exceeds the 99th '
                   'percentile of observations from 1960 to 1995')
    variables = ('pr',)
    conditions = {'pr__gt': F('map_cell__baseline__precip_99p')}


##########################
# Daily indicators

class DailyLowTemperature(TemperatureUnitsMixin, DailyRawIndicator):
    label = 'Daily Low Temperature'
    description = ('Daily low temperature averaged across all requested models')
    variables = ('tasmin',)


class DailyHighTemperature(TemperatureUnitsMixin, DailyRawIndicator):
    label = 'Daily High Temperature'
    description = ('Daily high temperature averaged across all requested models')
    variables = ('tasmax',)


class DailyPrecipitation(PrecipUnitsMixin, DailyRawIndicator):
    label = 'Daily Precipitation'
    description = ('Daily precipitation averaged across all requested models')
    variables = ('pr',)


def list_available_indicators():
    """ List the defined class members of this module as the available indicators """
    class_members = inspect.getmembers(sys.modules[__name__], inspect.isclass)
    indicators = [member[1] for member in class_members if member[1].__module__ == __name__]
    return [i.to_dict() for i in indicators]


def indicator_factory(indicator_name):
    """ Return a valid indicator class based on the string provided

    Given a lower case, underscore separated indicator name, return the class associated
    with it. e.g. yearly_frost_days -> indicators.models.YearlyFrostDays
    If no match found, return None

    """
    this_module = sys.modules[__name__]
    class_name = ''.join([s.capitalize() for s in indicator_name.split('_')])
    return getattr(this_module, class_name, None)
