from django.test import TestCase
from climate_data.models import (ClimateDataCell, ClimateModel, Scenario, ClimateDataSource,
                                 ClimateDataYear)
from indicators.partitioners import (YearlyPartitioner, MonthlyPartitioner, QuarterlyPartitioner,
                                     OffsetYearlyPartitioner, CustomPartitioner)


def float_range(start, stop):
    """Produce a list of consecutive floating point numbers, starting at start.

    Results are inclusive of start and stop, so 0 to 364 will produce 365 points.
    """
    return list(float(v) for v in range(start, stop + 1))


class PartitionTest(TestCase):
    def setUp(self):
        map_cell = ClimateDataCell.objects.create(lat=33.8, lon=-117.9)
        model = ClimateModel.objects.create(name='Test Model')
        scenario = Scenario.objects.create(name='Test Scenario')

        ClimateDataYear.objects.create(
            map_cell=map_cell,
            data_source=ClimateDataSource.objects.create(
                model=model,
                scenario=scenario,
                year=2051
            ),
            pr=float_range(0, 364),
            tasmin=float_range(10000, 10364),
            tasmax=float_range(20000, 20364)
        )
        ClimateDataYear.objects.create(
            map_cell=map_cell,
            data_source=ClimateDataSource.objects.create(
                model=model,
                scenario=scenario,
                year=2052
            ),
            pr=float_range(30000, 30365),
            tasmin=float_range(40000, 40365),
            tasmax=float_range(5000, 50365)
        )

    def test_yearly_partitions(self):
        partitioner = YearlyPartitioner(variables=['pr'])
        data = ClimateDataYear.objects.all()
        result = list(partitioner(data))
        self.assertEqual(result, [(2051, {'pr': float_range(0, 364)}),
                                  (2052, {'pr': float_range(30000, 30365)})])

    def test_monthly_partitions(self):
        partitioner = MonthlyPartitioner(variables=['pr'])
        data = ClimateDataYear.objects.filter(data_source__year=2051)
        result = list(partitioner(data))
        self.assertEqual(result, [('2051-01', {'pr': float_range(0, 30)}),
                                  ('2051-02', {'pr': float_range(31, 58)}),
                                  ('2051-03', {'pr': float_range(59, 89)}),
                                  ('2051-04', {'pr': float_range(90, 119)}),
                                  ('2051-05', {'pr': float_range(120, 150)}),
                                  ('2051-06', {'pr': float_range(151, 180)}),
                                  ('2051-07', {'pr': float_range(181, 211)}),
                                  ('2051-08', {'pr': float_range(212, 242)}),
                                  ('2051-09', {'pr': float_range(243, 272)}),
                                  ('2051-10', {'pr': float_range(273, 303)}),
                                  ('2051-11', {'pr': float_range(304, 333)}),
                                  ('2051-12', {'pr': float_range(334, 364)})])

    def test_quarterly_partitions(self):
        partitioner = QuarterlyPartitioner(variables=['pr'])
        data = ClimateDataYear.objects.filter(data_source__year=2051)
        result = list(partitioner(data))
        self.assertEqual(result, [('2051-Q1', {'pr': float_range(0, 89)}),
                                  ('2051-Q2', {'pr': float_range(90, 180)}),
                                  ('2051-Q3', {'pr': float_range(181, 272)}),
                                  ('2051-Q4', {'pr': float_range(273, 364)})])

    def test_offset_yearly_partition(self):
        partitioner = OffsetYearlyPartitioner(variables=['pr'])
        data = ClimateDataYear.objects.all()
        result = list(partitioner(data))
        self.assertEqual(result, [('2051-2052',
                                  {'pr': float_range(180, 364) + float_range(30000, 30179)})])

    def test_custom_partition_single_day(self):
        partitioner = CustomPartitioner(variables=['pr'], spans="6-1")
        data = ClimateDataYear.objects.filter(data_source__year=2051)
        result = list(partitioner(data))
        # June 1, 2051 is the 152nd day, and since values start at 0 it should have the 151 value
        self.assertEqual(result, [('2051-01', {'pr': [151.0]})])

    def test_custom_partition_single_day_leap_year(self):
        partitioner = CustomPartitioner(variables=['pr'], spans="6-1")
        data = ClimateDataYear.objects.filter(data_source__year=2052)
        result = list(partitioner(data))
        # June 1, 2052 is the 153rd day because it is a leap year
        # pr values for 2052 start with 30000 to differentiate them from other years in case of a
        # obscure collission bug.
        self.assertEqual(result, [('2052-01', {'pr': [30152.0]})])

    def test_custom_partition_base(self):
        partitioner = CustomPartitioner(variables=['pr'], spans="1-1:12-31")
        data = ClimateDataYear.objects.filter(data_source__year=2051)
        result = list(partitioner(data))
        self.assertEqual(result, [('2051-01', {'pr': float_range(0, 364)})])

    def test_custom_partition_complex(self):
        partitioner = CustomPartitioner(variables=['pr'], spans="3-14:3-20,6-5:9-30")
        data = ClimateDataYear.objects.filter(data_source__year=2051)
        result = list(partitioner(data))
        self.assertEqual(result,
                         # March 14, 2051 is day 73, March 20 is day 79 - less one for the index
                         [('2051-01', {'pr': float_range(72, 78)}),
                          # June 5 and September 30, 2051 are the 156th and 273rd days respectively
                          ('2051-02', {'pr': float_range(155, 272)})])

    def test_custom_partition_invalid_date(self):
        data = ClimateDataYear.objects.all()
        with self.assertRaises(AssertionError):
            partitioner = CustomPartitioner(variables=['pr'], spans="3-91")
            list(partitioner(data))

    def test_custom_partition_backwards_timespan(self):
        data = ClimateDataYear.objects.all()
        with self.assertRaises(AssertionError):
            partitioner = CustomPartitioner(variables=['pr'], spans="3-15:2-17")
            list(partitioner(data))

    def test_custom_partition_zero_day_of_month(self):
        data = ClimateDataYear.objects.all()
        with self.assertRaises(AssertionError):
            partitioner = CustomPartitioner(variables=['pr'], spans="3-0:3-2")
            list(partitioner(data))
