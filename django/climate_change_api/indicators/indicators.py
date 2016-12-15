import inspect
import sys
from itertools import groupby

from django.db.models import F, Sum, Avg, Max, Min

from .abstract_indicators import (YearlyAggregationIndicator, YearlyCountIndicator,
                                  YearlyMaxConsecutiveDaysIndicator, YearlySequenceIndicator,
                                  MonthlyAggregationIndicator, MonthlyCountIndicator,
                                  DailyRawIndicator, BasetempIndicatorMixin)
from .unit_converters import (TemperatureUnitsMixin, PrecipUnitsMixin, DaysUnitsMixin,
                              CountUnitsMixin, TemperatureDeltaUnitsMixin)


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


class YearlyDrySpells(CountUnitsMixin, YearlySequenceIndicator):
    label = 'Yearly Dry Spells'
    description = ('Total number of times per year that there are 5 or more consecutive ' +
                   'days without precipitation')
    variables = ('pr',)
    raw_condition = 'pr = 0'

    def aggregate(self):
        """ Calls get_streaks to get all sequences of zero or non-zero precip then counts
        the zero-precip ones that are at least 5 days long """
        sequences = self.get_streaks()
        for (model, year), streaks in groupby(sequences, self.row_group_key):
            num_dry_spells = sum(1 for seq in streaks if seq['match'] == 1 and seq['length'] >= 5)

            yield {'data_source__year': year,
                   'data_source__model': model,
                   'value': num_dry_spells}


class YearlyExtremePrecipitationEvents(CountUnitsMixin, YearlyCountIndicator):
    label = 'Yearly Extreme Precipitation Events'
    description = ('Total number of times per year daily precipitation exceeds the specified '
                   '(Default 99th) percentile of observations from 1960 to 1995')
    variables = ('pr',)
    parameters = {'percentile': 99}

    conditions = {'pr__gt': F('map_cell__baseline__pr')}

    @property
    def filters(self):
        return {'map_cell__baseline__percentile': self.parameters['percentile']}


class YearlyExtremeHeatEvents(CountUnitsMixin, YearlyCountIndicator):
    label = 'Yearly Extreme Heat Events'
    description = ('Total number of times per year daily maximum temperature exceeds the specified '
                   '(Default 99th) percentile of observations from 1960 to 1995')
    variables = ('tasmax',)
    parameters = {'percentile': 99}

    conditions = {'tasmax__gt': F('map_cell__baseline__tasmax')}

    @property
    def filters(self):
        return {'map_cell__baseline__percentile': self.parameters['percentile']}


class YearlyExtremeColdEvents(CountUnitsMixin, YearlyCountIndicator):
    label = 'Yearly Extreme Cold Events'
    description = ('Total number of times per year daily minimum temperature is below the specified '
                   '(Default 1st) percentile of observations from 1960 to 1995')
    variables = ('tasmin',)
    parameters = {'percentile': 1}

    conditions = {'tasmin__lt': F('map_cell__baseline__tasmin')}

    @property
    def filters(self):
        return {'map_cell__baseline__percentile': self.parameters['percentile']}


class YearlyHeatingDegreeDays(TemperatureDeltaUnitsMixin, BasetempIndicatorMixin,
                              YearlyAggregationIndicator):
    label = 'Yearly Heating Degree Days'
    description = ('Total difference of daily low temperature to a reference base temperature '
                   '(Default 65F)')
    variables = ('tasmin',)
    agg_function = Sum

    # List units as a parameter so it gets updated by the query params if it is overriden.
    # This way we can fall back to the units param if we need to handle bare numbers for basetemp
    parameters = {'basetemp': '65F',
                  'units': 'F'}

    @property
    def conditions(self):
        return {'tasmin__lte': self.parameters['basetemp']}

    @property
    def expression(self):
        return self.parameters['basetemp'] - F('tasmin')


class YearlyCoolingDegreeDays(TemperatureDeltaUnitsMixin, BasetempIndicatorMixin,
                              YearlyAggregationIndicator):
    label = 'Yearly Cooling Degree Days'
    description = ('Total difference of daily high temperature to a reference base temperature '
                   '(Default 65F)')
    variables = ('tasmax',)
    agg_function = Sum

    # List units as a parameter so it gets updated by the query params if it is overriden.
    # This way we can fall back to the units param if we need to handle bare numbers for basetemp
    parameters = {'basetemp': '65F',
                  'units': 'F'}

    @property
    def conditions(self):
            return {'tasmax__gte': self.parameters['basetemp']}

    @property
    def expression(self):
        return F('tasmax') - self.parameters['basetemp']


class HeatWaveDurationIndex(YearlyMaxConsecutiveDaysIndicator):
    label = 'Heat Wave Duration Index'
    description = ('Maximum period of consecutive days with daily high temperature greater than '
                   '5C above historic norm')
    variables = ('tasmax',)
    filters = {'day_of_year': F('map_cell__historic_average__day_of_year')}
    raw_condition = 'tasmax > avg_tasmax + 5'

    def aggregate(self):
        self.queryset = self.queryset.annotate(avg_tasmax=F('map_cell__historic_average__tasmax'))
        return super(HeatWaveDurationIndex, self).aggregate()


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
    description = ('Total number of times per month daily precipitation exceeds the specified '
                   '(Default 99th) percentile of observations from 1960 to 1995')
    variables = ('pr',)
    parameters = {'percentile': 99}

    conditions = {'pr__gt': F('map_cell__baseline__pr')}

    @property
    def filters(self):
        return {'map_cell__baseline__percentile': self.parameters['percentile']}


class MonthlyExtremeHeatEvents(CountUnitsMixin, MonthlyCountIndicator):
    label = 'Monthly Extreme Heat Events'
    description = ('Total number of times per month daily maximum temperature exceeds the specified '
                   '(Default 99th) percentile of observations from 1960 to 1995')
    variables = ('tasmax',)
    parameters = {'percentile': 99}

    conditions = {'tasmax__gt': F('map_cell__baseline__tasmax')}

    @property
    def filters(self):
        return {'map_cell__baseline__percentile': self.parameters['percentile']}


class MonthlyExtremeColdEvents(CountUnitsMixin, MonthlyCountIndicator):
    label = 'Monthly Extreme Cold Events'
    description = ('Total number of times per month daily minimum temperature is below the specified '
                   '(Default 1st) percentile of observations from 1960 to 1995')
    variables = ('tasmin',)
    parameters = {'percentile': 1}

    conditions = {'tasmin__lt': F('map_cell__baseline__tasmin')}

    @property
    def filters(self):
        return {'map_cell__baseline__percentile': self.parameters['percentile']}


class MonthlyHeatingDegreeDays(TemperatureDeltaUnitsMixin, BasetempIndicatorMixin,
                               MonthlyAggregationIndicator):
    label = 'Monthly Heating Degree Days'
    description = ('Total difference of daily low temperature to a reference base temperature '
                   '(Default 65F)')
    variables = ('tasmin',)
    agg_function = Sum

    # List units as a parameter so it gets updated by the query params if it is overriden.
    # This way we can fall back to the units param if we need to handle bare numbers for basetemp
    parameters = {'basetemp': '65F',
                  'units': 'F'}

    @property
    def conditions(self):
        return {'tasmin__lte': self.parameters['basetemp']}

    @property
    def expression(self):
        return self.parameters['basetemp'] - F('tasmin')


class MonthlyCoolingDegreeDays(TemperatureDeltaUnitsMixin, BasetempIndicatorMixin,
                               MonthlyAggregationIndicator):
    label = 'Monthly Cooling Degree Days'
    description = ('Total difference of daily high temperature to a reference base temperature '
                   '(Default 65F)')
    variables = ('tasmax',)
    agg_function = Sum

    # List units as a parameter so it gets updated by the query params if it is overriden.
    # This way we can fall back to the units param if we need to handle bare numbers for basetemp
    parameters = {'basetemp': '65F',
                  'units': 'F'}

    @property
    def conditions(self):
            return {'tasmax__gte': self.parameters['basetemp']}

    @property
    def expression(self):
        return F('tasmax') - self.parameters['basetemp']


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
