import calendar
import logging
from operator import itemgetter
from itertools import groupby

from .utils import sliding_window

from django.db.models import F
from django.conf import settings


logger = logging.getLogger(__name__)


class Partitioner(object):
    """Partition a sequence of ClimateDataYear data into the desired time aggregation.

    Add a value for 'agg_key' to each bucket to indicate how it should be rendered in the final
    result. It is possible for multiple results to have the same agg_key, which will be aggregated
    by the indicator's serializer
    """

    @classmethod
    def parse(cls, queryset):
        """Given a queryset of ClimateDataYear, return a sequence of dicts per time partition."""
        raise NotImplementedError()


class YearlyPartitioner(Partitioner):
    """Partition results by year.

    Since the ClimateDataYear is already partitioned, this is effectively a noop
    """

    @classmethod
    def parse(cls, queryset):
        return queryset.annotate(agg_key=F('data_source__year'))


class OffsetYearlyPartitioner(Partitioner):
    """Partition results by year, using an offset date to connect data from the previous year.

    Generates year-sized chunks that do not align with the Gregorian calendar's New Year. This
    requires splitting pairs of years in a sliding window, taking the latter half of one and the
    beginning half of the second. This will result in one fewer data point being returned than
    originated, as either the first or last will not half a partner to be combined with.

    By default uses day 180, so "Year 1" constitutes Year 0 day 181 through Year 1 day 180
    """

    offset = None

    def __init__(self, *args, **kwargs):
        self.offset = kwargs.pop('offset', 180)

        super(OffsetYearlyPartitioner, self).__init__(*args, **kwargs)

    def parse(self, queryset):
        """Given a queryset of ClimateDataYear, return a sequence of dicts per time partition."""
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
            year=F('data_source__year'), model=F('data_source__model_id')
        ).order_by('data_source__model_id', 'data_source__year')

        # Group models and sequential years together so we don't accidentally have our algorithm
        # compare years from different predictions or time periods.
        for years_group in group_consecutive_years(queryset):
            # Use a sliding window of width 2 so we have both years we need for each data point
            for prev, cur in sliding_window(years_group, n=2):
                # Remove model and year so only the variables' keys are left in the cur dictionary
                del cur['model']
                year = cur.pop('year')
                yield dict(
                    {
                        # Concatenate the trailing data of the previous year to the leading data
                        # of the current year
                        var: prev[var][self.offset + 1:] + cur[var][:self.offset]
                        for var in cur.keys()
                    },
                    agg_key=year
                )


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

    @classmethod
    def parse(cls, queryset):
        """Given a queryset of ClimateDataYear, return a sequence of dicts per time partition.

        This assumes that intervals existing entirely within years, and iterates across the interval
        sequence for each year in the result, producing a bucket for every iterval for every year.
        """
        queryset = queryset.annotate(year=F('data_source__year'))
        for bucket in queryset:
            year = bucket.pop('year')
            pos = 0
            for period, length in enumerate(cls.intervals(year), start=1):
                # This should never happen in production, but in testing we don't use full years
                #  which means there will be periods with 0 data points and can cause exceptions
                if any(pos > len(bucket[var]) for var in bucket):
                    if not settings.DEBUG:
                        logger.warn("Variable in bucket (%d, %d) contained less than %d values",
                                    year, period, pos)
                    break

                yield dict(
                    {
                        # use `pos` to move a window `length`-long along the variable's data
                        var: value[pos:pos + length - 1] for var, value in bucket.items()
                    },
                    agg_key=cls.agg_key(year, period)
                )
                pos += length


class MonthlyPartitioner(IntervalPartitioner):
    @classmethod
    def intervals(cls, year):
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


class QuarterlyPartitioner(IntervalPartitioner):
    @classmethod
    def intervals(cls, year):
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
