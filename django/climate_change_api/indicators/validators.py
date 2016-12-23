from django.core.exceptions import ValidationError


class IntRangeValidator(object):
    """ Validator which verifies that value is an integer and checks it against a range

    The range is inclusive, i.e. the provided minimum and maximum values are considered valid.

    """
    def __init__(self, minimum=0, maximum=100):
        self.minimum = minimum
        self.maximum = maximum

    def __call__(self, value):
        try:
            int_value = int(value)
        except (TypeError, ValueError) as e:
            raise ValidationError('{} is not an integer'.format(value))
        if int_value < self.minimum or int_value > self.maximum:
            raise ValidationError('{} must be in the range [{}, {}]'
                                  .format(value, self.minimum, self.maximum))


class TypeClassValidator(object):
    """ Validates that a value is of a particular type

    Argument type class should be a callable that takes a value and returns the value coerced
    to the desired type. If coercion fails, should raise a TypeError or ValueError.

    """
    def __init__(self, type_class):
        self.type_class = type_class

    def __call__(self, value):
        try:
            typed_value = self.type_class(value)
        except (TypeError, ValueError) as e:
            raise ValidationError('{} is not {}'.format(value, self.type_class))


class ChoicesValidator(object):
    """ Validator that checks to ensure a value is one of a limited set of options """
    def __init__(self, choices, is_null_allowed=False):
        self.choices = choices
        self.is_null_allowed = is_null_allowed

    def __call__(self, value):
        if value not in self.choices and not self.is_null_allowed:
            raise ValidationError('{} must be one of {}'.format(value, self.choices))


percentile_range_validator = IntRangeValidator(minimum=0, maximum=100)


integer_validator = TypeClassValidator(int)


float_validator = TypeClassValidator(float)
