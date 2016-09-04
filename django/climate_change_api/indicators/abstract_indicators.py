from collections import OrderedDict
import re


from climate_data.models import ClimateData
from climate_data.filters import ClimateDataFilterSet
from .serializers import IndicatorSerializer, YearlyIndicatorSerializer
from .unit_converters import TemperatureUnitsMixin


class Indicator(object):

    label = ''
    description = ''
    variables = ClimateData.VARIABLE_CHOICES
    filters = None
    serializer_class = IndicatorSerializer

    def __init__(self, city, scenario, models=None, years=None, units=None):
        if not city:
            raise ValueError('Indicator constructor requires a city instance')
        if not scenario:
            raise ValueError('Indicator constructor requires a scenario instance')

        self.city = city
        self.scenario = scenario
        self.models = models
        self.years = years

        # Validate and set desired units
        if units is None:
            self.units = self.default_units
        elif units not in self.available_units:
            raise ValueError('Cannot convert to requested units')
        else:
            self.units = units

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
            ('avaliable_units', cls.available_units),
            ('default_units', cls.default_units),
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
        if self.filters is not None:
            return self.queryset.filter(**self.filters)
        else:
            return self.queryset

    def aggregate(self):
        """ Calculate the indicator aggregation

        This method should use self.queryset to calculate the indicator returning a list of dicts
        that matches the form returned by the Django QuerySet `values` method
        """
        raise NotImplementedError('Indicator subclass must implement aggregate()')

    def convert(self, results):
        """ Convert aggregated results to the requested unit.

        @param results Dict returned by aggregate method
        @returns Dict in same format at results parameter, with values converted to `self.units`
        """
        if self.units == self.storage_units:
            return results
        converter = self.conversions[self.storage_units][self.units]
        for item in results:
            item['value'] = converter(item['value'])
        return results

    def calculate(self):
        results = self.aggregate()
        results = self.convert(results)
        return self.serializer.to_representation(results)


class YearlyIndicator(Indicator):
    """ Base class for yearly indicators. """
    serializer_class = YearlyIndicatorSerializer

    def get_values_qs(self):
        return self.queryset.values('data_source__year', 'data_source__model')


class YearlyAggregationIndicator(YearlyIndicator):
    def aggregate(self):
        return self.get_values_qs().annotate(value=self.agg_function(self.variables[0]))


