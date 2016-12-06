class ConverterTestMixin():
    def test_conversions(self):
        for units, tests in self.cases.iteritems():
            converter = self.converter_class.get(*units)

            for start, expected in tests:
                value = converter(start)
                self.assertAlmostEqual(value, expected,
                                       places=3,
                                       msg='Failed assertion that %f %s = %f %s, got %f %s' %
                                       (start, units[0], expected, units[1], value, units[1]))
