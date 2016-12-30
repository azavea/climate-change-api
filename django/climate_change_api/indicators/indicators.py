import inspect
import sys
from itertools import groupby

from django.db.models import F, Sum, Avg, Max, Min

from .abstract_indicators import (Indicator, CountIndicator, BasetempIndicatorMixin,
                                  YearlyMaxConsecutiveDaysIndicator, YearlySequenceIndicator)
from .params import DegreeDayIndicatorParams, Percentile1IndicatorParams, Percentile99IndicatorParams
from .unit_converters import (TemperatureUnitsMixin, PrecipUnitsMixin, DaysUnitsMixin,
                              CountUnitsMixin, TemperatureDeltaUnitsMixin, SECONDS_PER_DAY)


##########################
# Aggregated indicators

class AverageHighTemperature(TemperatureUnitsMixin, Indicator):
    label = 'Average High Temperature'
    description = ('Aggregated average high temperature, generated from daily data ' +
                   'using all requested models')
    variables = ('tasmax',)
    agg_function = Avg


class AverageLowTemperature(TemperatureUnitsMixin, Indicator):
    label = 'Average Low Temperature'
    description = ('Aggregated average low temperature, generated from daily data ' +
                   'using all requested models')
    variables = ('tasmin',)
    agg_function = Avg


class MaxHighTemperature(TemperatureUnitsMixin, Indicator):
    label = 'Maximum High Temperature'
    description = ('Maximum high temperature, generated from daily data ' +
                   'using all requested models')
    variables = ('tasmax',)
    agg_function = Max


class MinLowTemperature(TemperatureUnitsMixin, Indicator):
    label = 'Minimum Low Temperature'
    description = ('Minimum low temperature, generated from daily data ' +
                   'using all requested models')
    variables = ('tasmin',)
    agg_function = Min


class TotalPrecipitation(PrecipUnitsMixin, Indicator):
    label = 'Total Precipitation'
    description = 'Total precipitation'
    variables = ('pr',)
    # Precipitation is stored per-second, and we want a total for all days in the aggregation,
    # so we need to multiple each day's value by 86400 to get the total for that day and then
    # sum the results
    expression = F('pr') * SECONDS_PER_DAY
    agg_function = Sum


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
        """ Calls get_streaks to get all sequences of zero or non-zero precip then counts
        the zero-precip ones that are at least 5 days long """
        sequences = self.get_streaks()
        for key_vals, streaks in groupby(sequences, self.row_group_key):
            num_dry_spells = sum(1 for seq in streaks if seq['match'] == 1 and seq['length'] >= 5)

            yield dict(zip(self.aggregate_keys, key_vals) + [('value', num_dry_spells)])


class ExtremePrecipitationEvents(CountUnitsMixin, CountIndicator):
    label = 'Extreme Precipitation Events'
    description = ('Total number of times per period daily precipitation exceeds the specified '
                   'percentile of observations from 1960 to 1995')
    params_class = Percentile99IndicatorParams
    variables = ('pr',)

    conditions = {'pr__gt': F('map_cell__baseline__pr')}

    @property
    def filters(self):
        return {'map_cell__baseline__percentile': self.params.percentile.value}


class ExtremeHeatEvents(CountUnitsMixin, CountIndicator):
    label = 'Extreme Heat Events'
    description = ('Total number of times per period daily maximum temperature exceeds the '
                   'specified percentile of observations from 1960 to 1995')
    params_class = Percentile99IndicatorParams
    variables = ('tasmax',)

    conditions = {'tasmax__gt': F('map_cell__baseline__tasmax')}

    @property
    def filters(self):
        return {'map_cell__baseline__percentile': self.params.percentile.value}


class ExtremeColdEvents(CountUnitsMixin, CountIndicator):
    label = 'Extreme Cold Events'
    description = ('Total number of times per period daily minimum temperature is below the '
                   'specified percentile of observations from 1960 to 1995')
    params_class = Percentile1IndicatorParams
    variables = ('tasmin',)

    conditions = {'tasmin__lt': F('map_cell__baseline__tasmin')}

    @property
    def filters(self):
        return {'map_cell__baseline__percentile': self.params.percentile.value}


class HeatingDegreeDays(TemperatureDeltaUnitsMixin, BasetempIndicatorMixin, Indicator):
    label = 'Heating Degree Days'
    description = 'Total difference of daily low temperature to a reference base temperature'
    variables = ('tasmin',)
    agg_function = Sum
    params_class = DegreeDayIndicatorParams

    @property
    def conditions(self):
        return {'tasmin__lte': self.params.basetemp.value}

    @property
    def expression(self):
        return self.params.basetemp.value - F('tasmin')


class CoolingDegreeDays(TemperatureDeltaUnitsMixin, BasetempIndicatorMixin, Indicator):
    label = 'Cooling Degree Days'
    description = 'Total difference of daily high temperature to a reference base temperature '
    variables = ('tasmax',)
    agg_function = Sum
    params_class = DegreeDayIndicatorParams

    @property
    def conditions(self):
            return {'tasmax__gte': self.params.basetemp.value}

    @property
    def expression(self):
        return F('tasmax') - self.params.basetemp.value


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


def list_available_indicators():
    """ List the defined class members of this module as the available indicators """
    class_members = inspect.getmembers(sys.modules[__name__], inspect.isclass)
    indicators = [member[1] for member in class_members if member[1].__module__ == __name__]
    return [i.to_dict() for i in indicators]


def indicator_factory(indicator_name):
    """ Return a valid indicator class based on the string provided

    Given a lower case, underscore separated indicator name, return the class associated
    with it. e.g. frost_days -> indicators.models.FrostDays
    If no match found, return None

    """
    this_module = sys.modules[__name__]
    class_name = ''.join([s.capitalize() for s in indicator_name.split('_')])
    return getattr(this_module, class_name, None)
