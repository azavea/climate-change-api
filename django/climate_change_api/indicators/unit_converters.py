
class TemperatureUnitsMixin(object):
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


class PrecipUnitsMixin(object):
    """ Define units for precipitation

    The units are rates, so cumulative totals can be had either by averaging the rates then
    converting to the desired interval (i.e. average kg*m^2/s -> kg*m^2/year) or by converting
    to an interval and summing all values for that inveral across the desired interval
    (i.e. convert each day's rate to kg*m^2/day and sum across the days in the month or year)
    """
    available_units = ('kg*m^2/s', 'kg*m^2/day')
    storage_units = 'kg*m^2/s'
    default_units = 'kg*m^2/day'

    conversions = {
        'kg*m^2/s': {
            'kg*m^2/day': lambda x: x * 86400
        }
    }


class DaysUnitsMixin(object):
    available_units = ('days',)
    storage_units = 'days'
    default_units = 'days'


class CountUnitsMixin(object):
    available_units = ('count',)
    storage_units = 'count'
    default_units = 'count'
