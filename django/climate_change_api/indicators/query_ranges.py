from collections import namedtuple
import calendar

from django.db.models import Case, When, IntegerField, Value
from climate_data.models import ClimateDataSource


class QueryRangeConfig(object):
    """ Utility class to generate a Django Case object that converts day-of-year to a specific bucket
    """

    CaseRange = namedtuple('CaseRange', ('index', 'start', 'length'))
    range_config = None

    @staticmethod
    def get_years():
        """ Builds objects that categorize years by a common feature

        By default categorizes years by whether they are a leap year or not
        """
        all_years = set(ClimateDataSource.objects.distinct('year')
                                                 .values_list('year', flat=True))
        leap_years = set(filter(calendar.isleap, all_years))

        return [
            ('leap', leap_years),
            ('noleap', all_years - leap_years)
        ]

    @classmethod
    def get_intervals(cls, label):
        """ Returns an ordered series intervals to map days to interval segments

        Each value should be a tuple of (start, length), measured in day-of-year
        """
        raise NotImplementedError()

    @classmethod
    def make_ranges(cls, label):
        """ Takes the values of get_intervals and wraps them in CaseRange objects
        """
        cases = cls.get_intervals(label)
        return [cls.CaseRange(i, start, length)
                for (i, (start, length)) in enumerate(cases)]

    @classmethod
    def get_ranges(cls):
        """ Build mapping from day of year to month.

        Gets the year range by querying what data exists and builds CaseRange objects for each
        month.
        """
        return [
            {
                'years': years,
                'ranges': cls.make_ranges(label),
            }
            for (label, years) in cls.get_years()
        ]

    @classmethod
    def cases(cls):
        """ Generates a nested Case aggregation that assigns the month index to each
        data point.  It first splits on leap year or not then checks day_of_year against ranges.
        """
        if cls.range_config is None:
            cls.range_config = cls.get_ranges()

        year_whens = []
        for config in cls.range_config:
            case_whens = [When(**{
                'day_of_year__gte': case.start,
                'day_of_year__lt': case.start + case.length,
                'then': Value(case.index)
            }) for case in config['ranges']]
            year_whens.append(When(data_source__year__in=config['years'], then=Case(*case_whens)))
        return Case(*year_whens, output_field=IntegerField())


class LengthRangeConfig(QueryRangeConfig):
    """ RangeConfig based on a list of period lengths

    Assumes that the periods are consecutive, and that each period takes place immediately
    following the previous period.
    """
    lengths = {}

    @classmethod
    def get_intervals(cls, label):
        lengths = cls.lengths[label]
        return [(sum(lengths[:i]) + 1, lengths[i]) for i in range(len(lengths))]


class MonthRangeConfig(LengthRangeConfig):
    lengths = {
        'leap': [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31],
        'noleap': [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    }


class QuarterRangeConfig(LengthRangeConfig):
    lengths = {
        'leap': [91, 91, 92, 92],
        'noleap': [90, 91, 92, 92]
    }


class CustomRangeConfig(QueryRangeConfig):
    custom_spans = None

    @classmethod
    def day_of_year_from_date(cls, date, label):
        starts = {
            # These are all zero-based, so, for example, adding 1 for the 1st gives the true DOY
            'leap': [0, 31, 60, 91, 121, 152, 182, 213, 244, 274, 305, 335, 366],
            'noleap': [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334, 365]
        }.get(label)

        # Date is a tuple of month and day of month (DOM)
        month, dom = date

        # Offset calculations by a month because weird human dates start with 1
        doy = starts[month - 1] + dom
        # Make sure we have a non-zero DOM
        assert (dom > 0), "Invalid date provided"
        # Make sure this date exists in the month given
        assert (doy <= starts[month]), "Invalid date provided"

        return doy

    @classmethod
    def get_intervals(cls, label):
        # Spans are in the format MM-DD:MM-DD, so break those into nested tuples
        spans = [tuple(tuple(int(v) for v in date.split('-'))
                       for date in span.split(':'))
                 for span in cls.custom_spans.split(',')]

        for span in spans:
            start, end = (cls.day_of_year_from_date(date, label) for date in span)
            assert (start <= end), "Dates must be paired start:end"

            # Add one to end date because the end point is inclusive
            yield (start, end - start + 1)

    @classmethod
    def cases(cls, intervals):
        # Cases normally caches the range_config, but that's bad if the custom spans change
        # Check if that happened, and if it did clear the cached config
        if cls.custom_spans != intervals:
            cls.range_config = None
            cls.custom_spans = intervals

        return super(CustomRangeConfig, cls).cases()
