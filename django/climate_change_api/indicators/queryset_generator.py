from collections import namedtuple
import calendar

from django.db.models.functions import Concat
from django.db.models import Case, When, CharField, Value, F, Max, Min
from climate_data.models import ClimateData, ClimateDataSource
from climate_data.filters import ClimateDataFilterSet


def get(time_aggregation):
    """Provide the correct queryset generator class based on indicator time aggregation."""
    return {
        'monthly': MonthQuerysetGenerator,
        'quarterly': QuarterQuerysetGenerator,
        'yearly': YearQuerysetGenerator,
        'offset_yearly': OffsetYearQuerysetGenerator,
        'custom': CustomQuerysetGenerator
    }.get(time_aggregation)


class QuerysetGenerator(object):
    """Utility class to create querysets for ClimateData for a given time aggregation.

    Incorporates filtering by year as the year a data point is associated with can be dependant on
    the time aggregation used.
    """

    CaseRange = namedtuple('CaseRange', ('key', 'start', 'length'))
    range_config = None
    filterset_kwargs = {}

    @staticmethod
    def get_leap_year_sets():
        """Build objects that categorize years by a common feature.

        By default categorizes years by whether they are a leap year or not.
        """
        all_years = set(ClimateDataSource.objects.distinct('year')
                                                 .values_list('year', flat=True))
        leap_years = set(filter(calendar.isleap, all_years))

        return [
            ('leap', leap_years),
            ('noleap', all_years - leap_years)
        ]

    @classmethod
    def create_queryset(cls, scenario, years=None, models=None, key_params=None):
        if key_params is None:
            key_params = {}

        queryset = (ClimateData.objects.all()
                    .annotate(agg_key=cls.keys(**key_params))
                    .filter(agg_key__isnull=False,
                            data_source__scenario=scenario))

        if years is not None or models is not None:
            queryset = cls.apply_filters(queryset, years, models)

        return queryset

    @classmethod
    def apply_filters(cls, queryset, years, models):
        filterset = ClimateDataFilterSet(**cls.filterset_kwargs)
        queryset = filterset.filter_years(queryset, 'years', years)
        queryset = filterset.filter_models(queryset, 'models', models)
        return queryset

    @classmethod
    def get_interval_key(cls, index):
        return Concat(F('data_source__year'), Value('-{:02d}'.format(index + 1)))

    @classmethod
    def get_intervals(cls, label):
        """Return an ordered series intervals to map days to interval segments.

        Each value should be a tuple of (start, length), measured in day-of-year.
        """
        raise NotImplementedError()

    @classmethod
    def make_ranges(cls, label):
        """Take the values of get_intervals and wraps them in CaseRange objects."""
        cases = cls.get_intervals(label)
        return [cls.CaseRange(cls.get_interval_key(i), start, length)
                for (i, (start, length)) in enumerate(cases)]

    @classmethod
    def get_ranges(cls):
        """Build mapping from day of year to month.

        Gets the year range by querying what data exists and builds CaseRange objects for each
        month.
        """
        return [
            {
                'years': years,
                'ranges': cls.make_ranges(label),
            }
            for (label, years) in cls.get_leap_year_sets()
        ]

    @classmethod
    def keys(cls):
        """Generate a nested Case aggregation.

        Assigns the range key to each data point.
        It first splits on leap year or not then checks day_of_year against ranges.
        """
        if cls.range_config is None:
            cls.range_config = cls.get_ranges()

        year_whens = []
        for config in cls.range_config:
            case_whens = [When(**{
                'day_of_year__gte': case.start,
                'day_of_year__lt': case.start + case.length,
                'then': case.key
            }) for case in config['ranges']]
            year_whens.append(When(data_source__year__in=config['years'], then=Case(*case_whens)))
        return Case(*year_whens, output_field=CharField())


class YearQuerysetGenerator(QuerysetGenerator):
    """Special case generator for yearly annotations.

    Yearly annotations don't need any special logic, so we can short-circuit the whole process.
    """

    @classmethod
    def keys(cls):
        return F('data_source__year')


class LengthQuerysetGenerator(QuerysetGenerator):
    """QuerysetGenerator based on a list of period lengths.

    Assumes that the periods are consecutive, and that each period takes place immediately
    following the previous period.
    """

    lengths = {}

    @classmethod
    def get_intervals(cls, label):
        lengths = cls.lengths[label]
        return [(sum(lengths[:i]) + 1, lengths[i]) for i in range(len(lengths))]


class MonthQuerysetGenerator(LengthQuerysetGenerator):
    lengths = {
        'leap': [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31],
        'noleap': [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    }


class QuarterQuerysetGenerator(LengthQuerysetGenerator):
    @classmethod
    def get_interval_key(cls, index):
        return Concat(F('data_source__year'), Value('-Q{:0d}'.format(index + 1)))

    lengths = {
        'leap': [91, 91, 92, 92],
        'noleap': [90, 91, 92, 92]
    }


class CustomQuerysetGenerator(QuerysetGenerator):
    """QuerySet generator for user-defined date ranges within a given calendar year.

    Dates cannot span across year, OffsetYearQuerysetGenerator is necessary for that.
    """

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

        return super(CustomQuerysetGenerator, cls).cases()


class OffsetYearQuerysetGenerator(QuerysetGenerator):
    # By default place the year divide near the summer solstice to maximize the span that covers
    # winter
    custom_offset = 180
    filterset_kwargs = {'year_col': 'offset_year'}

    @classmethod
    def make_ranges(cls, label):
        """Build a pair of CaseRanges representing 366 day year split across two calendar years."""
        year_len = 366
        offset = cls.custom_offset
        return [
            # Include all days from the offset to New Years Eve
            cls.CaseRange(Concat(F('data_source__year'), Value('-'), F('data_source__year') + 1),
                          offset, year_len - offset + 1),
            # Start on New Years Day until the offset point the following year
            cls.CaseRange(Concat(F('data_source__year') - 1, Value('-'), F('data_source__year')),
                          0, offset)
        ]

    @classmethod
    def create_queryset(cls, *args, **kwargs):
        queryset = super(OffsetYearQuerysetGenerator, cls).create_queryset(*args, **kwargs)

        # Since we want to have complete year ranges, we want to conditionally remove the
        # beginning part of the first year and ending part of the last year to ensure all
        # results have complete data.
        # However, because ACCESS1-0, MIROC5, and bcc-csm1-1 don't have data for 2100, we need
        # specific logic to determine what constitutes the "first year" and "last year" for each
        # model.
        # To do this, we build a list of data sources that represent the first and last sources
        # for each model, and then filter so that we exclude those sources if the day is either
        # too early or too late to have another year to be paired with.
        first_year_sources = (ClimateDataSource.objects.all()
                              .annotate(minYear=Min('model__climatedatasource__year'))
                              .filter(year=F('minYear'))
                              .values('id'))
        last_year_sources = (ClimateDataSource.objects.all()
                             .annotate(maxYear=Max('model__climatedatasource__year'))
                             .filter(year=F('maxYear'))
                             .values('id'))
        queryset = (queryset
                    # Exclude data from the model's first year before the offset cutoff,
                    # and data from the model's last year after the cutoff
                    .exclude(data_source__in=first_year_sources, day_of_year__lt=cls.custom_offset)
                    .exclude(data_source__in=last_year_sources, day_of_year__gte=cls.custom_offset))

        return queryset

    @classmethod
    def apply_filters(cls, queryset, years, models):
        queryset = queryset.annotate(offset_year=Case(
            When(day_of_year__lt=cls.custom_offset,
                 then=F('data_source__year') - 1),
            default=F('data_source__year')))

        return super(OffsetYearQuerysetGenerator, cls).apply_filters(queryset, years, models)
