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
        all_years = set(ClimateDataSource.objects.distinct('year')
                                                 .values_list('year', flat=True))
        leap_years = set(filter(calendar.isleap, all_years))

        return [
            ('leap', leap_years),
            ('noleap', all_years - leap_years)
        ]

    @classmethod
    def make_ranges(cls, label):
        raise NotImplementedError()

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
                'day_of_year__lte': case.start + case.length,
                'then': Value(case.index)
            }) for case in config['ranges']]
            year_whens.append(When(data_source__year__in=config['years'], then=Case(*case_whens)))
        return Case(*year_whens, output_field=IntegerField())


class ContinuousRangeConfig(QueryRangeConfig):
    @classmethod
    def get_lengths(cls, label):
        raise NotImplementedError()

    @classmethod
    def make_ranges(cls, label):
        cases = cls.get_lengths(label)
        return [cls.CaseRange(i, sum(cases[:i])+1, cases[i]-1)
                for i in range(len(cases))]


class MonthRangeConfig(ContinuousRangeConfig):
    @classmethod
    def get_lengths(cls, label):
        months = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
        if label == 'leap':
            months[1] += 1
        return months


class QuarterRangeConfig(ContinuousRangeConfig):
    @classmethod
    def get_lengths(cls, label):
        lengths = [90, 91, 92, 92]
        if label == 'leap':
            lengths[0] += 1
        return lengths


class DiscreteRangeConfig(QueryRangeConfig):
    @classmethod
    def get_spans(cls, label):
        raise NotImplementedError()

    @classmethod
    def make_ranges(cls, label):
        cases = cls.get_spans(label)
        return [cls.CaseRange(i, start, end - start)
                for (i, (start, end)) in enumerate(cases)]


class CustomRangeConfig(DiscreteRangeConfig):
    custom_spans = None

    @staticmethod
    def day_of_year_from_date(date):
        # These are all zero-based, so, for example, adding 1 for the 1st gives the true DOY
        starts = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334]
        month, day = date
        date = starts[month - 1] + day
        assert (date < starts[month] + 1), "Invalid date provided"
        return date

    @classmethod
    def get_spans(cls, label):
        for span in cls.custom_spans:
            start, end = (cls.day_of_year_from_date(date) for date in span)
            assert (start <= end), "End date must come after start date"

            # Day 60 is normally March 1st, but in Leap Years it's February 29th
            # If the span crosses over the end of February, we might need to extend the end date
            if label == 'leap' and end >= 60:
                end += 1
                if start >= 60:
                    start += 1

            yield (start, end)

    @classmethod
    def cases(cls, intervals):
        # Cases normally caches the range_config, but that's bad if the custom spans change
        # Check if that happened, and if it did clear the cached config
        if cls.custom_spans != intervals:
            cls.range_config = None
            # Spans are in the format MM-DD:MM-DD, so break those into nested tuples
            cls.custom_spans = [tuple(tuple(int(v) for v in date.split('-'))
                                      for date in span.split(':'))
                                for span in intervals.split(',')]

        return super(CustomRangeConfig, cls).cases()
