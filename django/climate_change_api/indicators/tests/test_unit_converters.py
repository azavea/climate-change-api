from django.test import TestCase
from indicators.tests.mixins import ConverterTestMixin
from indicators.unit_converters import (TemperatureConverter, PrecipitationConverter,
                                        PrecipitationRateConverter)


class TemperatureConverterTestCase(ConverterTestMixin, TestCase):
    converter_class = TemperatureConverter
    cases = [
        {'F': -459.67, 'C': -273.15, 'K': 0},
        {'F': -40, 'C': -40, 'K': 233.15},
        {'F': 0, 'K': 255.372222, 'C': -17.77778},
        {'F': 32, 'C': 0, 'K': 273.15},
        {'F': 37.67, 'K': 276.3, 'C': 3.15},
        {'F': 71.87, 'C': 22.15, 'K': 295.3},
        {'F': 73.45, 'C': 23.027778, 'K': 296.17778},
        {'F': 73.76, 'C': 23.2, 'K': 296.35},
        {'F': 212, 'C': 100, 'K': 373.15}
    ]


class PrecipitationRateConverterTestCase(ConverterTestMixin, TestCase):
    converter_class = PrecipitationRateConverter
    cases = [
        {'kg/m^2/s': 1, 'kg/m^2/day': 86400},
        {'kg/m^2/s': 0.00001157407, 'kg/m^2/day': 1}
    ]


class PrecipitationConverterTestCase(ConverterTestMixin, TestCase):
    converter_class = PrecipitationConverter
    cases = [
        {'kg/m^2': 1, 'mm': 1, 'in': 0.0393701},
        {'kg/m^2': 25.4, 'mm': 25.4, 'in': 1},
        {'kg/m^2': 254, 'mm': 254, 'in': 10}
    ]
