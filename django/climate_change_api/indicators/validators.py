from datetime import datetime

from django.core.exceptions import ValidationError


class IntRangeValidator(object):
    """Validator which verifies that value is an integer and checks it against a range.

    The range is inclusive, i.e. the provided minimum and maximum values are considered valid.
    """

    def __init__(self, minimum=0, maximum=100):
        self.minimum = minimum
        self.maximum = maximum

    def __call__(self, value):
        try:
            int_value = int(value)
        except (TypeError, ValueError):
            raise ValidationError('{} is not an integer'.format(value))
        if int_value < self.minimum or int_value > self.maximum:
            raise ValidationError('{} must be in the range [{}, {}]'
                                  .format(value, self.minimum, self.maximum))


class TypeClassValidator(object):
    """Validates that a value is of a particular type.

    Argument type class should be a callable that takes a value and returns the value coerced
    to the desired type. If coercion fails, should raise a TypeError or ValueError.
    """

    def __init__(self, type_class):
        self.type_class = type_class

    def __call__(self, value):
        try:
            self.type_class(value)
        except (TypeError, ValueError):
            raise ValidationError('{} is not {}'.format(value, self.type_class))


class ChoicesValidator(object):
    """Validator that checks to ensure a value is one of a limited set of options."""

    def __init__(self, choices, is_null_allowed=False):
        self.choices = choices
        self.is_null_allowed = is_null_allowed

    def __call__(self, value):
        if value not in self.choices and not self.is_null_allowed:
            raise ValidationError('{} must be one of {}'.format(value, self.choices))


class CustomTimeParamValidator(object):
    """Validates custom_time_agg parameter of the Climate API.

    Checks to ensure that:
    - Date ranges are of the valid form MM-DD:MM-DD
    - Date ranges are always paired with a start and end
    - The start MM-DD is chronologically earlier than the end MM-DD

    Since our ranges are year agnostic, we always allow 2-29 to validate so that the
      day can be included for leap years.

    """

    ANY_LEAP_YEAR = 2000

    @classmethod
    def process_spans(cls, spans):
        """Split spans into tuples of mm-dd (start, end) pairs.

        Spans are strings of the form MM-DD:MM-DD,MM-DD
        """
        return (tuple(r.split(':')[:2]) for r in spans.split(','))

    def __call__(self, value):
        if value is None:
            return
        for date_range in self.process_spans(value):
            if len(date_range) != 2:
                raise ValidationError('Each date range must contain a start and end MM-DD')
            start_mm, start_dd = date_range[0].split('-')[:2]
            end_mm, end_dd = date_range[1].split('-')[:2]
            try:
                start_date = datetime(self.ANY_LEAP_YEAR, int(start_mm), int(start_dd))
                end_date = datetime(self.ANY_LEAP_YEAR, int(end_mm), int(end_dd))
            except ValueError:
                raise ValidationError('{}-{}:{}-{} must be a valid date range'
                                      .format(start_mm, start_dd, end_mm, end_dd))
            if start_date > end_date:
                raise ValidationError('{}-{} must be earlier than {}-{}'
                                      .format(start_mm, start_dd, end_mm, end_dd))


percentile_range_validator = IntRangeValidator(minimum=0, maximum=100)


integer_validator = TypeClassValidator(int)


float_validator = TypeClassValidator(float)
