
SECONDS_PER_DAY = 24 * 60 * 60
DAYS_PER_YEAR = 365.25
INCHES_PER_MILLIMETER = 1 / 25.4


class ConversionMixin(object):
    def getConverter(self, start, end):
        return lambda x: x


class TemperatureUnitsMixin(ConversionMixin):
    """ Define units for temperature conversion.
    """
    available_units = ('K', 'F', 'C')
    storage_units = 'K'
    default_units = 'F'

    conversions = {
        'K': {
            'F': lambda x: x * 1.8 - 459.67,
            'C': lambda x: x - 273.15
        }
    }

    def getConverter(self, start, end):
        if end == self.storage_units:
            return lambda x: x
        return self.conversions[start][end]


class PrecipUnitsMixin(ConversionMixin):
    """ Define units for precipitation

    The units are rates, so cumulative totals can be had either by averaging the rates then
    converting to the desired interval (i.e. average kg/m^2/s -> kg/m^2/year) or by converting
    to an interval and summing all values for that interval across the desired interval
    (i.e. convert each day's rate to kg/m^2/day and sum across the days in the month or year)

    The former is to be preferred, since the latter is basically doing part of this unit conversion
    by hand and will put the values out of sync with what the object believes its units to be.

    To convert from mass/area/second to height, we're assuming 1kg water == .001 m^3 which makes
    kg/m^2 equivalent to millimeters.
    """
    available_units = ('kg/m^2/s', 'kg/m^2/day', 'kg/m^2/year', 'in/day', 'in/year')
    storage_units = 'kg/m^2/s'
    default_units = 'in/day'

    conversions = {
        'kg/m^2/s': {
            'kg/m^2/day': lambda x: x * SECONDS_PER_DAY,
            'kg/m^2/year': lambda x: x * SECONDS_PER_DAY * DAYS_PER_YEAR,
            'in/day': lambda x: x * INCHES_PER_MILLIMETER * SECONDS_PER_DAY,
            'in/year': lambda x: x * INCHES_PER_MILLIMETER * SECONDS_PER_DAY * DAYS_PER_YEAR,
        }
    }

    def getConverter(self, start, end):
        if end == self.storage_units:
            return lambda x: x
        return self.conversions[start][end]


class DaysUnitsMixin(ConversionMixin):
    available_units = ('days',)
    storage_units = 'days'
    default_units = 'days'


class CountUnitsMixin(ConversionMixin):
    available_units = ('count',)
    storage_units = 'count'
    default_units = 'count'
