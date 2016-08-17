from django.db.models import Avg

from climate_data.models import ClimateData
from .serializers import IndicatorSerializer, YearlyIndicatorSerializer


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
        raise NotImplementedError('Indicator subclass must implement aggregate()')


class YearlyIndicator(Indicator):

    serializer_class = YearlyIndicatorSerializer


class YearlyAverageTemperatureIndicator(YearlyIndicator):

    def aggregate(self):
        variable = self.variables[0]
        return (self.queryset.values('data_source__year')
                             .annotate(value=Avg(variable)))
