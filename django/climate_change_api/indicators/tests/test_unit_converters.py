from django.test import TestCase
from indicators.tests.mixins import ConverterTestMixin
from indicators.unit_converters import TemperatureConverter, PrecipitationConverter


class TemperatureConverterTestCase(ConverterTestMixin, TestCase):
    converter_class = TemperatureConverter
    cases = {
        ('F', 'K'): [
            (0, 255.372222),
            (32, 273.15),
            (73.45, 296.17778)
        ],
        ('K', 'F'): [
            (0, -459.67),
            (276.3, 37.67)
        ],
        ('K', 'C'): [
            (0, -273.15),
            (295.3, 22.15)
        ],
        ('C', 'F'): [
            (-40, -40),
            (0, 32),
            (10, 50),
            (100, 212),
            (23.2, 73.76)
        ],
        ('F', 'C'): [
            (80, 26.6667),
            (73.2, 22.888889),
            (-40, -40),
            (0, -17.77778),
            (212, 100),
            (32, 0)
        ]
    }


class PrecipitationConverterTestCase(ConverterTestMixin, TestCase):
    converter_class = PrecipitationConverter
    cases = {
        ('kg/m^2/s', 'kg/m^2/day'): [
            (1, 86400)
        ],
        ('kg/m^2/day', 'kg/m^2/s'): [
            (86400, 1)
        ]
    }
