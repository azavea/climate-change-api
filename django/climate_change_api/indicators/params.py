from collections import OrderedDict

from django.core.exceptions import ValidationError
from climate_data.models import HistoricDateRange, ClimateDataset

from .unit_converters import TemperatureConverter
from .validators import (ChoicesValidator,
                         CustomTimeParamValidator,
                         float_validator,
                         percentile_range_validator)

MODELS_PARAM_DOCSTRING = ("A list of comma separated model names to filter the indicator by. The "
                          "indicator values in the response will only use the selected models. If "
                          "not provided, defaults to all models.")

DATASET_PARAM_DOCSTRING = ("A single value defining which provider to use for raw climate data. "
                           "If not provided, defaults to NEX-GDDP.")

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
                                    "'offset_yearly', 'quarterly', 'monthly', or 'custom'. "
                                    "Defaults to 'yearly'. If 'custom', 'custom_time_agg' "
                                    "parameter must be set.")

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

HISTORIC_RANGE_PARAM_DOCSTRING = ("The 30 year range of past years used to define the historic "
                                  "norm. Get the available options by querying the "
                                  "historic ranges endpoint. Defaults to the most recent "
                                  "period in the historical data.")

BASETEMP_PARAM_DOCSTRING = ("The base temperature used to calculate the daily difference for degree"
                            " days summations. Defaults to 65. See the 'basetemp_units' for a "
                            "discussion of the units this value uses.")

BASETEMP_UNITS_PARAM_DOCSTRING = "Units for the value of the 'basetemp' parameter. Defaults to 'F'."

THRESHOLD_PARAM_DOCSTRING = ("Required. The value against which to compare climate data values in"
                             " the unit specified by the 'threshold_units' parameter.")

THRESHOLD_UNITS_PARAM_DOCSTRING = ("Required. Units for the value of the 'threshold' parameter."
                                   " Must be a valid unit recognized by the API. Options: %s")

THRESHOLD_COMPARATOR_PARAM_DOCSTRING = ("Required. The comparison type against the value of the"
                                        " 'threshold' parameter. Options: lt, gt, lte, gte."
                                        " Signify: less than, greater than, less than or equals...")


class IndicatorParam(object):
    """Defines an individual query parameter for an Indicator request.

    @param name: The name of the query parameter
    @param description: Human readable descriptive help string describing use of the parameter
    @param required: Is this a required parameter?
    @param default: Default value to use for parameter if none provided
    @param validators: Array of functions or classes implementing the django.core.validators
                       interface, used to validate the parameter.
    @param empty_value: Input value that signals an empty value.
    """

    def __init__(self, name, description='', required=True, default=None, validators=None,
                 empty_value=''):
        self.name = name
        self.description = description
        self.required = required
        self.default = default
        self.validators = validators if validators is not None else []
        self.value = None
        self.serialized_value = None
        self.empty_value = empty_value

    def set_value(self, serialized_value):
        """Set value of parameter.

        Deserialize the passed value and save both it's serialized and deserialized
        representation after validation is passed.
        """
        if serialized_value is None:
            serialized_value = self.default
        deserialized = self.deserialize(serialized_value)
        self.validate(deserialized)
        self.serialized_value = serialized_value
        self.value = deserialized

    def deserialize(self, value):
        """Deserialize a value and return the result."""
        return value if value != self.empty_value else None

    def validate(self, value):
        """Validate the parameter by running all defined validators.

        Checks if param is required even if no validators are defined.

        Raises django.core.exceptions.ValidationError on the first failed validation check.
        """
        if value is None and self.required:
            raise ValidationError('{} is required.'.format(self.name))

        for v in self.validators:
            v(value)

    def to_dict(self):
        """Return complete representation of this class as a serializable dict.

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

    def __str__(self):
        """Return pretty string representation of model, used by Django for field labels."""
        return str(self.to_dict())


class CommaSeparatedIndicatorParam(IndicatorParam):
    def deserialize(self, value):
        """Deserialize a value and return the result."""
        return value.split(',') if value != self.empty_value else []


class IndicatorParams(object):
    """Superclass used to define parameters necessary for an Indicator class to function.

    Params can be defined either as class or instance variables. Prefer class variables
    if the IndicatorParam in question has no run-time dependencies.
    """

    models = CommaSeparatedIndicatorParam('models',
                                          description=MODELS_PARAM_DOCSTRING,
                                          required=False,
                                          default='all',
                                          validators=None,
                                          empty_value='all')
    years = CommaSeparatedIndicatorParam('years',
                                         description=YEARS_PARAM_DOCSTRING,
                                         required=False,
                                         default='all',
                                         validators=None,
                                         empty_value='all')
    agg = CommaSeparatedIndicatorParam('agg',
                                       description=AGG_PARAM_DOCSTRING,
                                       required=False,
                                       default='min,max,avg',
                                       validators=None)

    custom_time_agg = IndicatorParam('custom_time_agg',
                                     description=CUSTOM_TIME_AGG_PARAM_DOCSTRING,
                                     required=False,
                                     validators=[CustomTimeParamValidator()])

    def __init__(self, default_units, available_units, valid_aggregations):
        """Initialize additional params that are instance specific.

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
        self.dataset = IndicatorParam('dataset',
                                      description=DATASET_PARAM_DOCSTRING,
                                      required=False,
                                      default='NEX-GDDP',
                                      validators=[ChoicesValidator(ClimateDataset.datasets())])

    def set_parameters(self, parameters):
        """Set all parameters."""
        for param_class in self._get_params_classes():
            value = parameters.get(param_class.name, None)
            param_class.set_value(value)

    def to_dict(self):
        return [c.to_dict() for c in self._get_params_classes()]

    def _get_params_classes(self):
        """Return a list of the IndicatorParam instances defined on this class."""
        return sorted([getattr(self, x) for x in dir(self)
                      if isinstance(getattr(self, x), IndicatorParam)],
                      key=lambda c: c.name)

    def __str__(self):
        """Return pretty string representation of model, used by Django for field labels."""
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


class HistoricIndicatorParams(object):
    """Validate and set historic range, defaulting to most recent period.

    Stringify inputs and options for validator.
    """

    def __init__(self, *args, **kwargs):
        # TODO: Cache/save request results elsewhere to eliminate API calls per indicator call
        # Due to migrations issues, wwe can't set these as file globals
        default_pk = HistoricDateRange.objects.latest('end_year').pk  # Most recent
        avail_pks = [str(i['pk']) for i in HistoricDateRange.objects.all().values('pk')]
        historic_range_validator = ChoicesValidator(avail_pks)

        self.historic_range = IndicatorParam('historic_range',
                                             description=HISTORIC_RANGE_PARAM_DOCSTRING,
                                             required=False,
                                             default=str(default_pk),
                                             validators=[historic_range_validator])

        super(HistoricIndicatorParams, self).__init__(*args, **kwargs)


class ExtremeIndicatorParams(HistoricIndicatorParams, PercentileIndicatorParams):
    pass


class HeatWaveIndicatorParams(HistoricIndicatorParams, IndicatorParams):
    pass


class DegreeDayIndicatorParams(IndicatorParams):

    basetemp_units_validator = ChoicesValidator(TemperatureConverter.available_units)

    basetemp = IndicatorParam('basetemp',
                              description=BASETEMP_PARAM_DOCSTRING,
                              required=False,
                              default=65,
                              validators=[float_validator])

    basetemp_units = IndicatorParam('basetemp_units',
                                    description=BASETEMP_UNITS_PARAM_DOCSTRING,
                                    required=False,
                                    default='F',
                                    validators=[basetemp_units_validator])


class ThresholdIndicatorParams(IndicatorParams):

    valid_threshold_comparators = ('lt', 'lte', 'gt', 'gte')
    threshold_comparator_validator = ChoicesValidator(valid_threshold_comparators)
    threshold_units_validator = None

    threshold = IndicatorParam('threshold',
                               description=THRESHOLD_PARAM_DOCSTRING,
                               required=True,
                               validators=[float_validator])

    threshold_units = None

    threshold_comparator = IndicatorParam('threshold_comparator',
                                          description=THRESHOLD_COMPARATOR_PARAM_DOCSTRING,
                                          required=True,
                                          validators=[threshold_comparator_validator])

    def __init__(self, *args, **kwargs):
        threshold_units = kwargs.pop('threshold_units')
        self.threshold_units_validator = ChoicesValidator(threshold_units)
        self.threshold_units = IndicatorParam('threshold_units',
                                              description=THRESHOLD_UNITS_PARAM_DOCSTRING %
                                              (threshold_units,),
                                              required=True,
                                              validators=[self.threshold_units_validator])

        super(ThresholdIndicatorParams, self).__init__(*args, **kwargs)
