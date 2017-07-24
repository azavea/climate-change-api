import calendar
import logging
from operator import itemgetter
from itertools import groupby

from .utils import sliding_window

from django.db.models import F
from django.conf import settings


logger = logging.getLogger(__name__)


class Partitioner(object):
    """Partition a sequence of ClimateDataYear array data into the desired time aggregation.

    When invoked, takes a queryset filtered for the desired map cell, scenario, models and years,
    and returns an iterable of tuples of the form (aggregation_key, {var: [data], ...})

    Each tuple represents a single "bucket" of data, though multiple buckets may share the same
    aggregation key - these will be aggregated together by the indicator's serializer
    """

    variables = []

    def __init__(self, variables):
        self.variables = variables

    def __call__(self, queryset):
        """Partition a queryset into a iterable of tuples representing desired time periods."""
        queryset = queryset.values(*self.variables)
        return self.partition(queryset)

    def partition(self, queryset):
        raise NotImplementedError()


class YearlyPartitioner(Partitioner):
    """Partition results by year."""

    def partition(self, queryset):
        queryset = queryset.annotate(year=F('data_source__year'))
        for row in queryset.iterator():
            yield (row['year'], {var: row[var] for var in self.variables})


class OffsetYearlyPartitioner(Partitioner):
    """Partition results by year, using an offset date to connect data from the previous year.

    Generates year-sized chunks that do not align with the Gregorian calendar's New Year. This
    requires splitting pairs of years in a sliding window, taking the latter half of one and the
    beginning half of the second. This will result in one fewer data point being returned than
    originated, as either the first or last will not half a partner to be combined with.

    By default uses day 180, so "Year 0-1" constitutes Year 0 day 181 through Year 1 day 180
    """

    offset = None

    def __init__(self, *args, **kwargs):
        self.offset = kwargs.pop('offset', 180)

        super(OffsetYearlyPartitioner, self).__init__(*args, **kwargs)

    def partition(self, queryset):
        """Process a queryset of ClimateDataYear into a sequence of dicts per time partition."""
        def group_consecutive_years(results):
            """Group queryset results into chains of consecutive years of the same model."""
            def match_function(obj):
                index, row = obj
                # Measure the offset of the year from the index... consecutive years will have
                # consecutive indexes, giving them the same offset and so the same group
                return (row['model'], index - row['year'])
            for _, group in groupby(enumerate(results), match_function):
                # Remove the enumeration from each result in the group
                yield map(itemgetter(1), group)

        # We need to know year and model so we can make sure we don't accidentally merge unrelated
        # years
        queryset = queryset.annotate(
            year=F('data_source__year'),
            model=F('data_source__model_id'),
            scenario=F('data_source__scenario_id')
        ).order_by('data_source__model_id', 'data_source__year')
        it = queryset.iterator()

        # Group models and sequential years together so we don't accidentally have our algorithm
        # compare years from different predictions or time periods.
        for years_group in group_consecutive_years(it):
            # Use a sliding window of width 2 so we have both years we need for each data point
            for prev, cur in sliding_window(years_group, n=2):
                agg_key = "{}-{}".format(cur['year'] - 1, cur['year'])
                data = {var: prev[var][self.offset:] + cur[var][:self.offset]
                        for var in self.variables}
                yield (agg_key, data)


class IntervalPartitioner(Partitioner):
    """Partition results based on the day of year, for both leap as well as non-leap years."""

    @classmethod
    def intervals(cls, year):
        """Return a sequence of interval lengths for the specified year.

        Lengths represent contigious partitions starting at day 0 and should encompass the entire
        year.
        """
        raise NotImplementedError()

    @classmethod
    def agg_key(cls, year, period):
        """Return a string representing how the bucket should be shown in the final serialization.

        For instance, quarterly partitioning should produce buckets with aggregation keys like:
         2050-Q1
         2091-Q3
         etc
        """
        raise NotImplementedError()

    def partition(self, queryset):
        """Given a queryset of ClimateDataYear, return a sequence of tuples per time partition.

        This assumes that intervals existing entirely within years, and iterates across the interval
        sequence for each year in the result, producing a bucket for every interval for every year.
        """
        queryset = queryset.annotate(year=F('data_source__year'))
        for bucket in queryset.iterator():
            year = bucket.pop('year')
            for period, interval in enumerate(self.intervals(year), start=1):
                start, stop = interval
                # This should never happen in production, but in testing we don't use full years
                #  which means there will be periods with 0 data points and can cause exceptions
                if any(start > len(bucket[var]) for var in bucket):
                    if not settings.DEBUG:
                        logger.warn("Variable in bucket (%d, %d) contained less than %d values",
                                    year, period, start)
                    break

                yield (self.agg_key(year, period),
                       # use start and stop to choose the interval to output
                       {var: value[start:stop] for var, value in bucket.items()})


class LengthPartitioner(IntervalPartitioner):
    def intervals(self, year):
        lengths = self.lengths(year)
        pos = 0
        for l in lengths:
            yield (pos, pos + l)
            pos += l


class MonthlyPartitioner(LengthPartitioner):
    @classmethod
    def lengths(cls, year):
        """Return the length of the months in the year, depending if it's a leap year or not."""
        return {
            # Leap year month lengths
            True: [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31],
            # Normal year month lengths
            False: [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
        }.get(calendar.isleap(year))

    @classmethod
    def agg_key(cls, year, month):
        """Key monthly buckets by YYYY-MM."""
        return '%04d-%02d' % (year, month)


class QuarterlyPartitioner(LengthPartitioner):
    @classmethod
    def lengths(cls, year):
        """Return the length of the quarters in the year, depending if it's a leap year or not."""
        return {
            # Leap year quarter lengths
            True: [91, 91, 92, 92],
            # Normal year quarter lengths
            False: [90, 91, 92, 92]
        }.get(calendar.isleap(year))

    @classmethod
    def agg_key(cls, year, quarter):
        """Key quarterly buckets by YYYY-Q[1-4]."""
        return '%04d-Q%d' % (year, quarter)


class CustomPartitioner(IntervalPartitioner):
    def __init__(self, *args, **kwargs):
        self.spans = kwargs.pop('spans')
        super(CustomPartitioner, self).__init__(*args, **kwargs)

    def agg_key(self, year, period):
        """Key monthly buckets by YYYY-MM."""
        return '%04d-%02d' % (year, period)

    def intervals(self, year):
        for term in self.process_spans():
            if len(term) == 1:
                index = self.day_index(term[0], year)
                yield (index, index + 1)
            else:
                start, stop = [self.day_index(date, year) for date in term]
                assert start <= stop, "Start date must precede end date"
                yield (start, stop + 1)

    def day_index(self, date, year):
        """Convert a string of the form MM-DD to an index (day-of-year minus one) for that year."""
        month_start_offset = {
            # Offset for the first day of the month for each day in a leap year
            True: [0, 31, 60, 91, 121, 152, 182, 213, 244, 274, 305, 335, 366],
            # Offset for the first day of the month for each day in a conventional year
            False: [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334, 365]
        }.get(calendar.isleap(year))

        month, dom = [int(part) for part in date.split('-', 1)]

        # Offset calculations by a month and a day because weird human dates start with 1
        doy = month_start_offset[month - 1] + dom - 1
        # Make sure we have a non-zero DOM
        assert (dom > 0), "Invalid date provided"
        # Make sure this date exists in the month given
        assert (doy <= month_start_offset[month]), "Invalid date provided"

        return doy

    def process_spans(self):
        return (tuple(range.split(':', 1)) for range in self.spans.split(','))
