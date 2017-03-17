from django.core.exceptions import ValidationError
from django.test import TestCase

from indicators.validators import ChoicesValidator, IntRangeValidator


class ValidatorTestCase(TestCase):

    def should_succeed_with_value(self, validator, value):
        """Raise failure if validator(value) should succeed but fails."""
        try:
            validator(value)
        except ValidationError as e:
            self.fail(str(e))


class IntRangeValidatorTestCase(ValidatorTestCase):

    def test_valid(self):
        v = IntRangeValidator(minimum=0, maximum=5)
        self.should_succeed_with_value(v, 3)

    def test_handle_strings(self):
        v = IntRangeValidator(minimum=0, maximum=5)
        self.should_succeed_with_value(v, '3')
        with self.assertRaises(ValidationError):
            v('notanumber')

    def test_range_edges(self):
        v = IntRangeValidator(minimum=0, maximum=5)
        self.should_succeed_with_value(v, 0)
        self.should_succeed_with_value(v, 5)

    def test_out_of_range(self):
        v = IntRangeValidator(minimum=0, maximum=5)
        with self.assertRaises(ValidationError):
            v(-1)
        with self.assertRaises(ValidationError):
            v(6)


class ChoicesValidatorTestCase(ValidatorTestCase):

    def setUp(self):
        self.default_choices = ('a', 'b', 'c',)

    def test_valid(self):
        v = ChoicesValidator(self.default_choices)
        self.should_succeed_with_value(v, 'a')

    def test_invalid(self):
        v = ChoicesValidator(self.default_choices)
        with self.assertRaises(ValidationError):
            v('notinchoices')

    def test_int_types(self):
        v = ChoicesValidator((1, 2, 3,))
        self.should_succeed_with_value(v, 1)
        with self.assertRaises(ValidationError):
            v(5)

    def test_null_allowed(self):
        v = ChoicesValidator(self.default_choices, is_null_allowed=True)
        self.should_succeed_with_value(v, None)

        v = ChoicesValidator(self.default_choices, is_null_allowed=False)
        with self.assertRaises(ValidationError):
            v(None)

    def test_mixed_types(self):
        v = ChoicesValidator(('a', 1,))
        self.should_succeed_with_value(v, 'a')
        self.should_succeed_with_value(v, 1)
        with self.assertRaises(ValidationError):
            v('b')
        with self.assertRaises(ValidationError):
            v(5)
