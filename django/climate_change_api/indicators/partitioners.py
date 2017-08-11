import calendar
import logging
from operator import itemgetter
from itertools import groupby

from .validators import CustomTimeParamValidator
from .utils import sliding_window

from django.conf import settings


logger = logging.getLogger(__name__)

LEAP_YEAR_MONTH_LENGTHS = [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
CONVENTIONAL_YEAR_MONTH_LENGTHS = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]


class Partitioner(object):
    """Partition a sequence of ClimateDataYear array data into the desired time aggregation.

    When invoked, takes a iterator of (year, values) tuples and returns an iterable of tuples of the
    desired time aggregation in the form (aggregation_key, {var: [data], ...})
    """

    def __init__(self):
        pass

    def __call__(self, it):
        """Partition a iterable of (year, data) tuples into the desired time periods."""
        raise NotImplementedError()


class YearlyPartitioner(Partitioner):
    """Partition results by year."""

    def __call__(self, it):
        # Yearly data is already partitioned
        return it


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

    def __call__(self, it):
        """Process a  of ClimateDataYear into a sequence of dicts per time partition."""
        def group_consecutive_years(results):
            """Group iterator tuples into chains of consecutive years."""
            def match_function(obj):
                index, row = obj
                # Measure the offset of the year from the index... consecutive years will have
                # consecutive indexes, giving them the same offset and so the same group
                return index - row[0]
            for _, group in groupby(enumerate(results), match_function):
                # Remove the enumeration from each result in the group
                yield map(itemgetter(1), group)

        # Group sequential years together so we don't accidentally merge data from unrelated years
        # into the same partition
        for years_group in group_consecutive_years(it):
            # Use a sliding window of width 2 so we have both years we need for each data point
            for prev, cur in sliding_window(years_group, n=2):
                prev_year, prev_data = prev
                cur_year, cur_data = cur
                agg_key = "{}-{}".format(prev_year, cur_year)
                data = {var: prev_data[var][self.offset:] + cur_data[var][:self.offset]
                        for var in cur_data.keys()}
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

    def __call__(self, it):
        """Given a iterator of (year, values) tuples, return a sequence of tuples per time partition.

        This assumes that intervals existing entirely within years, and iterates across the interval
        sequence for each year in the result, producing a bucket for every interval for every year.
        """
        for year, data in it:
            for period, interval in enumerate(self.intervals(year), start=1):
                start, stop = interval
                # This should never happen in production, but in testing we don't use full years
                #  which means there will be periods with 0 data points and can cause exceptions
                if any(start > len(data[var]) for var in data):
                    if not settings.DEBUG:
                        logger.warn("Variable in bucket (%d, %d) contained less than %d values",
                                    year, period, start)
                    break

                yield (self.agg_key(year, period),
                       # use start and stop to choose the interval to output
                       {var: values[start:stop] for var, values in data.items()})


class LengthPartitioner(IntervalPartitioner):

    @classmethod
    def lengths(cls, year):
        """Return an array containing the number of days in each bucket length.

        For a concrete example, a partitioner that returns an aggregated value for each quarter
        of the calendar year would return something like [90, 91, 92, 92] for non-leap years.

        """
        raise NotImplementedError()

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
        if calendar.isleap(year):
            return LEAP_YEAR_MONTH_LENGTHS
        else:
            return CONVENTIONAL_YEAR_MONTH_LENGTHS

    @classmethod
    def agg_key(cls, year, month):
        """Key monthly buckets by YYYY-MM."""
        return '%04d-%02d' % (year, month)


class QuarterlyPartitioner(LengthPartitioner):
    @classmethod
    def lengths(cls, year):
        """Return the length of the quarters in the year, depending if it's a leap year or not."""
        if calendar.isleap(year):
            return [91, 91, 92, 92]
        else:
            return [90, 91, 92, 92]

    @classmethod
    def agg_key(cls, year, quarter):
        """Key quarterly buckets by YYYY-Q[1-4]."""
        return '%04d-Q%d' % (year, quarter)


class CustomPartitioner(IntervalPartitioner):
    # Spans are a user-defined string of sets of MM-DD, either alone or as a range like MM-DD:MM-DD
    # joined together by commas, like MM-DD,MM-DD:MM-DD
    spans = None

    def __init__(self, *args, **kwargs):
        self.spans = kwargs.pop('spans')
        super(CustomPartitioner, self).__init__(*args, **kwargs)

    def agg_key(self, year, period):
        """Key monthly buckets by YYYY-MM."""
        return '%04d-%02d' % (year, period)

    def intervals(self, year):
        for term in CustomTimeParamValidator.process_spans(self.spans):
            if len(term) == 1:
                index = self.day_index(term[0], year)
                yield (index, index + 1)
            else:
                start, stop = [self.day_index(date, year) for date in term]
                assert start <= stop, "Start date must precede end date"
                yield (start, stop + 1)

    def day_index(self, date, year):
        """Convert a string of the form MM-DD to an index (day-of-year minus one) for that year."""
        if calendar.isleap(year):
            month_lengths = LEAP_YEAR_MONTH_LENGTHS
        else:
            month_lengths = CONVENTIONAL_YEAR_MONTH_LENGTHS

        # Offset day and month values by one because human dates have to be special
        month, dom = [int(part) - 1 for part in date.split('-', 1)]

        # Make sure we have a positive DOM
        assert (dom >= 0), "Invalid date provided"
        # Make sure this date exists in the month given
        assert (dom < month_lengths[month]), "Invalid date provided"

        month_start_offset = sum(month_lengths[:month])

        doy = month_start_offset + dom

        return doy
