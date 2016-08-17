import sys

from .abstract_indicators import YearlyAverageTemperatureIndicator


class YearlyAverageMaxTemperature(YearlyAverageTemperatureIndicator):

    variables = ('tasmax',)


class YearlyAverageMinTemperature(YearlyAverageTemperatureIndicator):

    variables = ('tasmin',)


# class YearlyFrostDays(YearlyIndicator):
#     """ TODO: Fix this indicator, its busted. It requires aggregating this aggregation """

#     variables = ('tasmin',)

#     def aggregate(self):
#         variable = self.variables[0]
#         return (self.queryset.filter(tasmin__lt=273.15)
#                              .values('data_source__year', 'data_source__model')
#                              .annotate(value=Count(variable)))


def indicator_factory(indicator_name):
    """ Return a valid indicator class based on the string provided

    Given a lower case, underscore separated indicator name, return the class associated
    with it. e.g. yearly_frost_days -> indicators.models.YearlyFrostDays
    If no match found, return None

    """
    this_module = sys.modules[__name__]
    class_name = ''.join([s.capitalize() for s in indicator_name.split('_')])
    return getattr(this_module, class_name, None)
