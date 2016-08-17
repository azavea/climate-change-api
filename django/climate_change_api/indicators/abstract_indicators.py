from django.db.models import Avg

from climate_data.models import ClimateData
from climate_data.filters import ClimateDataFilterSet
from .serializers import IndicatorSerializer, YearlyIndicatorSerializer


class Indicator(object):

    variables = ClimateData.VARIABLE_CHOICES
    serializer_class = IndicatorSerializer

    def __init__(self, city, scenario, models=None, years=None):
        if not city:
            raise ValueError('Indicator constructor requires a city instance')
        if not scenario:
            raise ValueError('Indicator constructor requires a scenario instance')

        self.models = models
        self.years = years

        self.queryset = (ClimateData.objects.filter(map_cell=city.map_cell)
                                            .filter(data_source__scenario=scenario))
        self.queryset = self.filter_objects()

        self.serializer = self.serializer_class()

    def filter_objects(self):
        """ A subclass can override this to further filter the dataset before calling calculate """
        filter_set = ClimateDataFilterSet()
        self.queryset = filter_set.filter_years(self.queryset, self.years)
        self.queryset = filter_set.filter_models(self.queryset, self.models)
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
