import sys

from django.db.models import Avg, Count

from climate_data.models import ClimateData
from indicators.serializers import IndicatorSerializer, YearlyIndicatorSerializer


class Indicator(object):

    variables = ClimateData.VARIABLE_CHOICES
    serializer_class = IndicatorSerializer

    def __init__(self, city, scenario, models=None, years=None):
        if not city:
            raise ValueError('Indicator constructor requires a city instance')
        if not scenario:
            raise ValueError('Indicator constructor requires a scenario instance')

        self.models = self._validate_models(models)
        self.years = self._validate_years(years)

        self.queryset = (ClimateData.objects.filter(map_cell=city.map_cell)
                                            .filter(data_source__scenario=scenario))
        self.queryset = self.filter_objects()

        self.serializer = self.serializer_class()

    def _validate_models(self, model_list):
        return model_list

    def _validate_years(self, year_list):
        return year_list

    def filter_objects(self):
        """ A subclass can override this to further filter the dataset before calling calculate """
        return self.queryset

    def calculate(self):
        results = self.aggregate()
        return self.serializer.to_representation(results)

    def aggregate(self):
        """ Calculate the indicator aggregation

        This method should use self.queryset to calculate the indicator returning a dict
        that matches the form returned by the Django QuerySet annotate method

        """
        raise NotImplementedError('')


class YearlyIndicator(Indicator):

    serializer_class = YearlyIndicatorSerializer


class YearlyAverageTemperatureIndicator(YearlyIndicator):

    def aggregate(self):
        variable = self.variables[0]
        return (self.queryset.values('data_source__year')
                             .annotate(value=Avg(variable)))


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
