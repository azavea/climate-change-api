import calendar
import logging

from django.db.models import F
from django.conf import settings

"""Partition a sequence of ClimateDataYear data into the desired time aggregation

Add a value for 'agg_key' to each bucket to indicate how it should be rendered in the final result.
It is possible for multiple results to have the same agg_key, which will be aggregated by the
indicator's serializer
"""

logger = logging.getLogger(__name__)


class YearlyPartitioner(object):
    """Partition results by year.

    Since the ClimateDataYear is already partitioned, this is effectively a noop
    """

    @classmethod
    def parse(cls, queryset):
        return queryset.annotate(agg_key=F('data_source__year'))


class IntervalPartitioner(object):
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
