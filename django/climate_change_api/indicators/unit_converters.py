from django.utils.decorators import classproperty

SECONDS_PER_DAY = 24 * 60 * 60
DAYS_PER_YEAR = 365.25
INCHES_PER_MILLIMETER = 1 / 25.4


##########################
# Unit converters

class UnitConverter(object):
    units = {}

    @classmethod
    def create(cls, start, end):
        raise NotImplementedError()

    @classmethod
    def get(cls, start, end):
        """Instantiate a converter if necessary via factory method.

        In cases where we're doing a noop conversion, instead we'll return a pass-through lambda.
        """
        if start == end:
            # We're not doing a conversion, so no need to create a converter class
            return lambda x: x

        # Create a lamdba for converting these specific units
        return cls.create(start, end)

    @classproperty
    def available_units(cls):
        return list(cls.units.keys())


class LinearConverter(UnitConverter):
    @classmethod
    def create(cls, start, end):
        ratio = 1.0 * cls.units[end] / cls.units[start]

        return lambda x: x * ratio


class OffsetLinearConverter(UnitConverter):
    @classmethod
    def create(cls, start, end):
        start_x, start_r = cls.units[start]
        end_x, end_r = cls.units[end]

        ratio = 1.0 * end_r / start_r
        offset = (1.0 * end_x / ratio) - start_x

        return lambda x: (x + offset) * ratio


class TemperatureConverter(OffsetLinearConverter):
    units = {
        'F': (-459.67, 1.8),
        'C': (-273.15, 1),
        'K': (0, 1)
    }


class TemperatureDeltaConverter(LinearConverter):
    """Specialized version of TemperatureConverter to convert a degree temperature as a quantity.

    This does not adjust for different 0-points. That is, 1 degree Centigrade is equal to exactly
    1.8 degrees Fahrenheit.
    """

    units = {
        'C': 1,
        'F': 1.8,
        'K': 1
    }


class PrecipitationRateConverter(LinearConverter):
    """Define units for rate of precipitation.

    To convert from mass/area/second to height, we're assuming 1kg water == .001 m^3 which makes
    kg/m^2 equivalent to millimeters.
    """

    units = {
        'kg/m^2/s': 1,
        'kg/m^2/day': SECONDS_PER_DAY,
        'in/day': INCHES_PER_MILLIMETER * SECONDS_PER_DAY,
    }


class PrecipitationConverter(LinearConverter):
    """Define units for precipitation.

    Internally precipitation is stored as mass per area per time, but for total precipitation
    we need to present the result as a fixed amount... either a mass per area or linear distance.

    To convert from mass/area to height, we're assuming 1kg water == .001 m^3 which makes
    kg/m^2 equivalent to millimeters.
    """

    units = {
        'kg/m^2': 1,
        'mm': 1,
        'in': INCHES_PER_MILLIMETER
    }


##########################
# Mixin classes

class ConversionMixin(object):
    converter_class = UnitConverter

    def getConverter(self, start, end):
        return self.converter_class.get(start, end)

    @classproperty
    def available_units(cls):
        return cls.converter_class.available_units


class TemperatureUnitsMixin(ConversionMixin):
    """Define units for temperature conversion."""

    converter_class = TemperatureConverter
    storage_units = 'K'
    default_units = 'F'


class TemperatureDeltaUnitsMixin(TemperatureUnitsMixin):
    """Uses the same units as the TemperatureUnitsMixin, but doesn't adjust for 0-point offset."""

    converter_class = TemperatureDeltaConverter


class PrecipUnitsMixin(ConversionMixin):
    converter_class = PrecipitationConverter
    storage_units = 'kg/m^2'
    default_units = 'in'


class PrecipRateUnitsMixin(ConversionMixin):
    converter_class = PrecipitationRateConverter
    storage_units = 'kg/m^2/s'
    default_units = 'in/day'


class DaysUnitsMixin(ConversionMixin):
    available_units = ('days',)
    storage_units = 'days'
    default_units = 'days'


class CountUnitsMixin(ConversionMixin):
    available_units = ('count',)
    storage_units = 'count'
    default_units = 'count'
