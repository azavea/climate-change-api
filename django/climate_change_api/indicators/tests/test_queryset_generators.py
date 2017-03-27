from django.test import TestCase
from indicators.queryset_generator import (MonthQuerysetGenerator, QuarterQuerysetGenerator,
                                           CustomQuerysetGenerator)


class LengthQuerysetGenerator(object):
    generator = None

    def test_length_config(self):
        total = sum(self.generator.lengths['noleap'])
        self.assertEqual(total, 365)

        total = sum(self.generator.lengths['leap'])
        self.assertEqual(total, 366)

    def test_get_intervals(self):
        for label, result in self.intervals.items():
            intervals = self.generator.get_intervals(label)
            self.assertEqual(intervals, result)


class QuarterQuerysetGeneratorTestCase(LengthQuerysetGenerator, TestCase):
    generator = QuarterQuerysetGenerator
    intervals = {
        'leap': [(1, 91), (92, 91), (183, 92), (275, 92)],
        'noleap': [(1, 90), (91, 91), (182, 92), (274, 92)]
    }


class MonthQuerysetGeneratorTestCase(LengthQuerysetGenerator, TestCase):
    generator = MonthQuerysetGenerator
    intervals = {
        'leap': [(1, 31), (32, 29), (61, 31), (92, 30), (122, 31), (153, 30), (183, 31), (214, 31),
                 (245, 30), (275, 31), (306, 30), (336, 31)],
        'noleap': [(1, 31), (32, 28), (60, 31), (91, 30), (121, 31), (152, 30), (182, 31),
                   (213, 31), (244, 30), (274, 31), (305, 30), (335, 31)]
    }


class CustomQuerysetGeneratorTestCase(TestCase):
    def test_non_leap_year(self):
        CustomQuerysetGenerator.custom_spans = "1-1:12-31"
        intervals = list(CustomQuerysetGenerator.get_intervals('noleap'))
        self.assertEqual(intervals, [(1, 365)])

        CustomQuerysetGenerator.custom_spans = "5-13:5-31,7-8:12-14"
        intervals = list(CustomQuerysetGenerator.get_intervals('noleap'))
        self.assertEqual(intervals, [(133, 19), (189, 160)])

    def test_invalid(self):
        with self.assertRaises(AssertionError):
            CustomQuerysetGenerator.custom_spans = "1-56:1-57"
            list(CustomQuerysetGenerator.get_intervals('noleap'))

        with self.assertRaises(AssertionError):
            CustomQuerysetGenerator.custom_spans = "7-0:9-2"
            list(CustomQuerysetGenerator.get_intervals('noleap'))

        with self.assertRaises(AssertionError):
            CustomQuerysetGenerator.custom_spans = "7-1:5-1"
            list(CustomQuerysetGenerator.get_intervals('noleap'))
