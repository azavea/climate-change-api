import inspect
import sys

from .abstract_indicators import YearlyAverageTemperatureIndicator


class YearlyAverageMaxTemperature(YearlyAverageTemperatureIndicator):

    label = 'Yearly Average Max Temperature'
    description = ('Aggregated yearly average maximum temperature, generated from daily data ' +
                   'using all requested models')
    variables = ('tasmax',)


class YearlyAverageMinTemperature(YearlyAverageTemperatureIndicator):

    label = 'Yearly Average Min Temperature'
    description = ('Aggregated yearly average minimum temperature, generated from daily data ' +
                   'using all requested models')
    variables = ('tasmin',)


# class YearlyFrostDays(YearlyIndicator):
#     """ TODO: Fix this indicator, its busted. It requires aggregating this aggregation """

#     description = ('Number of days per year in which the minimum daily temperature is ' +
#                    'less than the melting point of water (273.15K)')
#     variables = ('tasmin',)

#     def aggregate(self):
#         variable = self.variables[0]
#         return (self.queryset.filter(tasmin__lt=273.15)
#                              .values('data_source__year', 'data_source__model')
#                              .annotate(value=Count(variable)))


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
