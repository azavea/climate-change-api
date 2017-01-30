from itertools import permutations


class ConverterTestMixin():
    def test_conversions(self):
        for case in self.cases:
            # Test all possible combinations and ensure that they all convert properly
            for units, values in (list(zip(*v)) for v in permutations(list(case.items()), 2)):
                converter = self.converter_class.get(*units)

                start, expected = values
                actual = converter(start)

                self.assertAlmostEqual(actual, expected,
                                       places=3,
                                       msg='Failed assertion that %f %s = %f %s, got %f %s' %
                                       (start, units[0], expected, units[1], actual, units[1]))
