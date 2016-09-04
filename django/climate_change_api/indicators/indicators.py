import inspect
import sys

from django.db import connection
from django.db.models import Avg, Max, Min, Sum

from .abstract_indicators import YearlyAggregationIndicator
from .unit_converters import (TemperatureUnitsMixin, PrecipUnitsMixin,
                              DaysUnitsMixin, CountUnitsMixin)


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
    description = 'Yearly total precipitation'
    variables = ('pr',)
    agg_function = Sum




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
