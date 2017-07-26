from django.test import TestCase
from indicators.utils import merge_dicts, sliding_window, running_total


class MergeDictsTestCase(TestCase):
    def test_merge_dicts(self):
        a = {'a': 5}
        b = {'b': 7}
        c = merge_dicts(a, b)
        self.assertEqual(c, {'a': 5, 'b': 7})
        self.assertEqual(a, {'a': 5})
        self.assertEqual(b, {'b': 7})


class SlidingWindowTestCase(TestCase):
    def test_window(self):
        it = [1, 2, 3]
        windows = list(sliding_window(it, n=2))
        self.assertEqual(windows, [(1, 2), (2, 3)])

    def test_too_short_window(self):
        it = [1, 2, 3]
        windows = list(sliding_window(it, n=4))
        # Have 3 points but ask for a window 4 wide, so we should get nothing
        self.assertEqual(windows, [])

    def test_empty_window(self):
        it = []
        windows = list(sliding_window(it, n=2))
        self.assertEqual(windows, [])


def RunningTotalTestCase(TestCase):
    def test_empty_sequence(self):
        it = []
        totals = list(running_total(it))
        self.assertEqual(totals, [])

    def test_increasing_range(self):
        it = [1, 2, 3, 4]
        totals = list(running_total(it))
        self.assertEqual(totals, [1, 3, 6, 10])

    def test_floor(self):
        it = [1, 2, -100, 3]
        totals = list(running_total(it, floor=0))
        self.assertEqual(totals, [1, 3, 0, 3])
