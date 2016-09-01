from collections import OrderedDict
import re

from django.db.models import Avg

from climate_data.models import ClimateData
from climate_data.filters import ClimateDataFilterSet
from .serializers import IndicatorSerializer, YearlyIndicatorSerializer


class Indicator(object):

    label = ''
    description = ''
    variables = ClimateData.VARIABLE_CHOICES
    serializer_class = IndicatorSerializer

    def __init__(self, city, scenario, models=None, years=None):
        if not city:
            raise ValueError('Indicator constructor requires a city instance')
        if not scenario:
            raise ValueError('Indicator constructor requires a scenario instance')

        self.city = city
        self.scenario = scenario
        self.models = models
        self.years = years

        self.queryset = self.get_queryset()
        self.queryset = self.filter_objects()

        self.serializer = self.serializer_class()

    @classmethod
    def name(cls):
        def convert(name):
            """ Convert caps case string to snake case, e.g. IndicatorClass -> indicator_class """
            s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
            return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
        return convert(cls.__name__)

    @classmethod
    def to_dict(cls):
        """ Return a dict representation of the indicator """
        return OrderedDict([
            ('name', cls.name()),
            ('label', cls.label),
            ('description', cls.description),
            ('variables', cls.variables),
        ])

    def get_queryset(self):
        """ Get the initial indicator queryset

        ClimateData initially filtered by city/scenario and optionally years/models as passed
        by the constructor

        """
        filter_set = ClimateDataFilterSet()
        queryset = (ClimateData.objects.filter(map_cell=self.city.map_cell)
                                       .filter(data_source__scenario=self.scenario))
        queryset = filter_set.filter_years(queryset, self.years)
        queryset = filter_set.filter_models(queryset, self.models)
        return queryset

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
