from collections import OrderedDict
import re

from django.db.models import Avg

from climate_data.models import ClimateData
from climate_data.filters import ClimateDataFilterSet
from .serializers import IndicatorSerializer, YearlyIndicatorSerializer


def kelvin_to_fahrenheit(value):
    """ Convenience method to handle converting temperatures to degrees Fahrenheit.
    """
    return value * 1.8 - 459.67


class Indicator(object):

    label = ''
    description = ''
    variables = ClimateData.VARIABLE_CHOICES
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

    def to_dict(self):
        """ Return a dict representation of the indicator """
        return OrderedDict([
            ('name', self.name()),
            ('label', self.label),
            ('description', self.description),
            ('variables', self.variables),
            ('avalialbe_units', self.available_units()),
            ('default_unit', self.default_unit()),
        ])

    @property
    def available_units(self):
        """ Provide the units in which this indicator may return its values as upper-case strings.
        Must contain the string returned by `default_unit()`.
        @returns tuple of strings
        """
        raise NotImplementedError('Indicator subclass must implement available_units()')

    @property
    def default_unit(self):
        """ @returns default unit for indicator values

        This method should return an upper-case string contained in the tuple returned by
        `available_units()`. If requested unit is the default unit, no conversion will be performed.
        """
        raise NotImplementedError('Indicator subclass must implement default_unit()')

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
        if self.units:
            if self.units not in self.available_units():
                raise ValueError('Indicator cannot be converted to the unit requested')
            elif self.units.upper() != self.default_unit().upper():
                results = self.convert(results, self.units.upper())
        return self.serializer.to_representation(results)

    def aggregate(self):
        """ Calculate the indicator aggregation

        This method should use self.queryset to calculate the indicator returning a dict
        that matches the form returned by the Django QuerySet annotate method

        """
        raise NotImplementedError('Indicator subclass must implement aggregate()')

    def convert(self, results, units):
        """ Convert aggregated results to the requested unit.

        This method must handle converting from `default_unit()` to each of the other units listed
        in `available_units()`.

        @param results Dict returned by aggregate method
        @param units String of unit to convert into. Must be contained in `available_units()`.
        @returns Dict in same format at results parameter, with converted values
        """
        raise NotImplementedError('Indicator subclass must implement convert()')


class TemperatureUnitsMixin(Indicator):
    """ Define units for temperature conversion.
    """

    def available_units(self):
        return ('K', 'F')

    def default_unit(self):
        return 'K'


class YearlyIndicator(Indicator):

    serializer_class = YearlyIndicatorSerializer


class YearlyAverageTemperatureIndicator(YearlyIndicator, TemperatureUnitsMixin):

    def aggregate(self):
        variable = self.variables[0]
        return (self.queryset.values('data_source__year')
                             .annotate(value=Avg(variable)))

    def convert(self, results, units):
        if units == 'F':
            for year in results:
                year['value'] = kelvin_to_fahrenheit(year['value'])
        else:
            raise ValueError('Cannot convert YearlyAverageTemperatureIndicator to requested units')

        return results
