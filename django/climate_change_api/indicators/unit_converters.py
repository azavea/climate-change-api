

def kelvin_to_fahrenheit(value):
    """ Convenience method to handle converting temperatures to degrees Fahrenheit.
    """
    return value * 1.8 - 459.67


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
