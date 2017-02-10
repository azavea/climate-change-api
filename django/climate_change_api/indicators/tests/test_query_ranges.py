from django.test import TestCase
from indicators.query_ranges import MonthQuerysetGenerator, QuarterQuerysetGenerator, CustomQuerysetGenerator


class QuarterQueryRangeTestCase(TestCase):
    def test_non_leap_year(self):
        intervals = QuarterQuerysetGenerator.get_intervals('noleap')
        self.assertEqual(intervals, [(1, 90), (91, 91), (182, 92), (274, 92)])

    def test_leap_year(self):
        intervals = QuarterQuerysetGenerator.get_intervals('leap')
        self.assertEqual(intervals, [(1, 91), (92, 91), (183, 92), (275, 92)])


class MonthQueryRangeTestCase(TestCase):
    def test_non_leap_year(self):
        intervals = MonthQuerysetGenerator.get_intervals('noleap')
        self.assertEqual(intervals, [(1, 31),
                                     (32, 28),
                                     (60, 31),
                                     (91, 30),
                                     (121, 31),
                                     (152, 30),
                                     (182, 31),
                                     (213, 31),
                                     (244, 30),
                                     (274, 31),
                                     (305, 30),
                                     (335, 31)])

    def test_leap_year(self):
        intervals = MonthQuerysetGenerator.get_intervals('leap')
        self.assertEqual(intervals, [(1, 31),
                                     (32, 29),
                                     (61, 31),
                                     (92, 30),
                                     (122, 31),
                                     (153, 30),
                                     (183, 31),
                                     (214, 31),
                                     (245, 30),
                                     (275, 31),
                                     (306, 30),
                                     (336, 31)])


class CustomQueryRangeTestCase(TestCase):
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
