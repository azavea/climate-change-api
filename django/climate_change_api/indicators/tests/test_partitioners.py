from django.test import TestCase
from climate_data.models import (ClimateDataCell, ClimateModel, Scenario, ClimateDataSource,
                                 ClimateDataYear)
from indicators.partitioners import (YearlyPartitioner, MonthlyPartitioner, QuarterlyPartitioner,
                                     OffsetYearlyPartitioner)


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
