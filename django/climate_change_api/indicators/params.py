from collections import OrderedDict

from django.core.exceptions import ValidationError

from .unit_converters import TemperatureConverter
from .validators import ChoicesValidator, float_validator, percentile_range_validator

MODELS_PARAM_DOCSTRING = ("A list of comma separated model names to filter the indicator by. The "
                          "indicator values in the response will only use the selected models. If "
                          "not provided, defaults to all models.")

YEARS_PARAM_DOCSTRING = ("A list of comma separated year ranges to filter the response by. "
                         "Defaults to all years available. A year range is of the form "
                         "'start[:end]'. Examples: '2010', '2010:2020', '2010:2020,2030', "
                         "'2010:2020,2030:2040'")

AGG_PARAM_DOCSTRING = ("A list of comma separated aggregation types to return. Valid choices are "
                       "'min', 'max', 'avg', 'median', 'stddev', 'stdev', and 'XXth'. If using "
                       "'XXth', replace the XX with a number between 1-99 to return that "
                       "percentile. For example, '99th' returns the value of the 99th percentile. "
                       "The 'XXth' option can be provided multiple times with different values. "
                       "'stdev' is an alias to 'stddev'. Defaults to 'min,max,avg'.")

TIME_AGGREGATION_PARAM_DOCSTRING = ("Time granularity to group data by for result structure. Valid "
                                    "aggregations depend on indicator. Can be 'yearly', "
                                    "'quarterly', 'monthly', 'daily' or 'custom'. Defaults to "
                                    "'yearly'. If 'custom', 'custom_time_agg' parameter must be "
                                    "set.")

UNITS_PARAM_DOCSTRING = ("Units in which to return the data. Defaults to Imperial units (Fahrenheit"
                         " for temperature indicators and inches for precipitation).")

CUSTOM_TIME_AGG_PARAM_DOCSTRING = ("Used in conjunction with the 'custom' time_aggregation value. "
                                   "A list of comma separated month-day pairs defining the time "
                                   "intervals to aggregate within. Data points will only be "
                                   "assigned to one aggregation, and for overlapping intervals the"
                                   " interval defined first will take precedence. Dates are "
                                   "formmatted MM-DD and pairs are formatted 'start:end'. Examples:"
                                   " '3-1:5-31', '1-1:6-30,7-1:12-31'")

PERCENTILE_PARAM_DOCSTRING = ("The percentile threshold used to determine the appropriate "
                              "comparative level of an event or measurement. Must be an integer in "
                              "the range [0,100]. Defaults to %d")


THRESHOLD_PARAM_DOCSTRING = ("The value against which to compare climate data values. Unit assumed 'units' param"
                             "else the indicator default unit.")

THRESHOLD_UNITS_PARAM_DOCSTRING = ("Threshold unit type")

THRESHOLD_COMPARATOR_PARAM_DOCSTRING = ("The comparison type against the threshold value. Options: lt, gt, lte, gte, e"
                                  "Signify: less than, greater than, less than or equals...")

class IndicatorParam(object):
    """ Defines an individual query parameter for an Indicator request

    @param name: The name of the query parameter
    @param description: Human readable descriptive help string describing use of the parameter
    @param required: Is this a required parameter?
    @param default: Default value to use for parameter if none provided
    @param validators: Array of functions or classes implementing the django.core.validators
                       interface, used to validate the parameter.

    """
    def __init__(self, name, description='', required=True, default=None, validators=None):
        self.name = name
        self.description = description
        self.required = required
        self.default = default
        self.validators = validators if validators is not None else []
        self.value = None

    def validate(self, value):
        """ Validates the parameter by running all defined validators

        Checks if param is required even if no validators are defined.

        Raises django.core.exceptions.ValidationError on the first failed validation check.

        """
        value = value if value is not None else self.default
        if value is None and self.required:
            raise ValidationError('{} is required.'.format(self.name))

        for v in self.validators:
            v(value)
        self.value = value

    def to_dict(self):
        """ Return complete representation of this class as a serializable dict

        Makes the IndicatorParam class self documenting.

        """
        description = OrderedDict([
            ('name', self.name),
            ('description', self.description),
            ('required', self.required),
        ])
        if self.default is not None:
            description['default'] = self.default
        return description

    def __repr__(self):
        return str(self.to_dict())


class IndicatorParams(object):
    """ Superclass used to define parameters necessary for an Indicator class to function

    Params can be defined either as class or instance variables. Prefer class variables
    if the IndicatorParam in question has no run-time dependencies.

    """
    models = IndicatorParam('models',
                            description=MODELS_PARAM_DOCSTRING,
                            required=False,
                            validators=None)
    years = IndicatorParam('years',
                           description=YEARS_PARAM_DOCSTRING,
                           required=False,
                           validators=None)
    agg = IndicatorParam('agg',
                         description=AGG_PARAM_DOCSTRING,
                         required=False,
                         default='min,max,avg',
                         validators=None)

    custom_time_agg = IndicatorParam('custom_time_agg',
                                     description=CUSTOM_TIME_AGG_PARAM_DOCSTRING,
                                     required=False,
                                     validators=None)

    def __init__(self, default_units, available_units, valid_aggregations):
        """ Initialize additional params that are instance specific

        Would love a workaround so that we don't have to do this, and can define all params
        statically. But, units has defaults/choices that are specific to the indicator and params
        we're validating, so we can't do that here.

        """
        available_units_validator = ChoicesValidator(available_units)
        valid_aggregations_validator = ChoicesValidator(valid_aggregations)
        self.units = IndicatorParam('units',
                                    description=UNITS_PARAM_DOCSTRING,
                                    required=False,
                                    default=default_units,
                                    validators=[available_units_validator])
        self.time_aggregation = IndicatorParam('time_aggregation',
                                               description=TIME_AGGREGATION_PARAM_DOCSTRING,
                                               required=False,
                                               default='yearly',
                                               validators=[valid_aggregations_validator])

    def validate(self, parameters):
        """ Validate all parameters """
        for param_class in self._get_params_classes():
            value = parameters.get(param_class.name, None)
            param_class.validate(value)

    def to_dict(self):
        return [c.to_dict() for c in self._get_params_classes()]

    def _get_params_classes(self):
        """ Return a list of the IndicatorParam instances defined on this class """
        return sorted([getattr(self, x) for x in dir(self)
                      if isinstance(getattr(self, x), IndicatorParam)],
                      key=lambda c: c.name)

    def __repr__(self):
        return str(self.to_dict())


class PercentileIndicatorParams(IndicatorParams):
    percentile = None

    def __init__(self, *args, **kwargs):
        percentile = kwargs.pop('percentile')
        self.percentile = IndicatorParam('percentile',
                                         description=PERCENTILE_PARAM_DOCSTRING % (percentile,),
                                         required=False,
                                         default=percentile,
                                         validators=[percentile_range_validator])

        super(PercentileIndicatorParams, self).__init__(*args, **kwargs)


class ThresholdIndicatorParams(IndicatorParams):

    valid_threshold_comparators = ('lt', 'lte', 'gt', 'gte', 'e', 'none')
    threshold_comparator_validator = ChoicesValidator(valid_threshold_comparators)

    threshold = IndicatorParam('threshold',
                               description=THRESHOLD_PARAM_DOCSTRING,
                               required=False,
                               default=0,
                               validators=[float_validator])

    threshold_units = IndicatorParam('threshold_units',
                                     description=THRESHOLD_UNITS_PARAM_DOCSTRING,
                                     required=False)

    threshold_comparator = IndicatorParam('threshold_comparator',
                                          description=THRESHOLD_COMPARATOR_PARAM_DOCSTRING,
                                          required=False,
                                          default='none',
                                          validators=[threshold_comparator_validator])
