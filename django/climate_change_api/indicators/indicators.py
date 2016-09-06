import inspect
import sys

from django.db import connection
from django.db.models import Avg, Max, Min, Sum

from .abstract_indicators import (YearlyAggregationIndicator, YearlyCountIndicator, int_avg)
from .unit_converters import (TemperatureUnitsMixin, PrecipUnitsMixin,
                              DaysUnitsMixin, CountUnitsMixin)


class YearlyAverageHighTemperature(TemperatureUnitsMixin, YearlyAggregationIndicator):
    label = 'Yearly Average High Temperature'
    description = ('Aggregated yearly average high temperature, generated from daily data ' +
                   'using all requested models')
    variables = ('tasmax',)
    agg_function = Avg


class YearlyAverageLowTemperature(TemperatureUnitsMixin, YearlyAggregationIndicator):
    label = 'Yearly Average Low Temperature'
    description = ('Aggregated yearly average low temperature, generated from daily data ' +
                   'using all requested models')
    variables = ('tasmin',)
    agg_function = Avg


class YearlyMaxHighTemperature(TemperatureUnitsMixin, YearlyAggregationIndicator):
    label = 'Yearly Maximum High Temperature'
    description = ('Yearly maximum high temperature, generated from daily data ' +
                   'using all requested models')
    variables = ('tasmax',)
    agg_function = Max


class YearlyMinLowTemperature(TemperatureUnitsMixin, YearlyAggregationIndicator):
    label = 'Yearly Minimum Low Temperature'
    description = ('Yearly minimum low temperature, generated from daily data ' +
                   'using all requested models')
    variables = ('tasmin',)
    agg_function = Min


class YearlyTotalPrecipitation(PrecipUnitsMixin, YearlyAggregationIndicator):
    description = 'Yearly total precipitation'
    variables = ('pr',)
    agg_function = Sum


class YearlyFrostDays(DaysUnitsMixin, YearlyCountIndicator):
    description = ('Number of days per year in which the minimum daily temperature is ' +
                   'less than the melting point of water (273.15K)')
    variables = ('tasmin',)
    filters = {'tasmin__lt': 273.15}


class YearlyMaxConsecutiveDryDays(DaysUnitsMixin, YearlyCountIndicator):
    description = ('Maximum number of consecutive days with no precipitation per year')
    variables = ('pr',)

    def calculate(self):
        """
        Uses a query to partition the data series into consecutive days with the same amount of
        precip and return all streaks sorted by year, model, streak length. Then picks the longest
        where the amount is zero for each year and model, then averages across models.

        Starts from the existing queryset with year/model/etc filters already applied.

        Filtering by precip amount is done in code because if it were done in the query we would
        get no results for years/models with no dry spells.
        """
        (base_query, base_query_params) = (self.queryset.select_related('data_source')
                                               .query.sql_with_params())
        query = """
            SELECT year as data_source__year, model_id as data_source__model, count(*) as length, pr
            FROM (SELECT year, model_id, day_of_year, pr,
                         ROW_NUMBER() OVER(ORDER BY year, model_id, day_of_year) -
                         ROW_NUMBER() OVER(PARTITION BY pr ORDER BY year, model_id, day_of_year)
                         AS grp
                  FROM ({base_query}) orig_query) groups
            GROUP BY year, model_id, grp, pr
        """.format(base_query=base_query)
        with connection.cursor() as cursor:
            cursor.execute(query, base_query_params)
            columns = [col[0] for col in cursor.description]
            sequences = [dict(zip(columns, row)) for row in cursor.fetchall()]
        longest = {}
        for seq in sequences:
            year = longest.setdefault(seq['data_source__year'], {})
            year.setdefault(seq['data_source__model'], 0)
            if seq['pr'] == 0 and seq['length'] > year[seq['data_source__model']]:
                year[seq['data_source__model']] = seq['length']
        results = {yr: int_avg([length for length in models.values()])
                   for (yr, models) in longest.items()}
        return results


class YearlyDrySpells(CountUnitsMixin, YearlyCountIndicator):
    description = ('Total number of times per year that there are 5 or more consecutive ' +
                   'days without precipitation')
    variables = ('pr',)

    def calculate(self):
        """ Since filtering for precip in the query means we get no data for a year/model if
        there were zero dry days, this pulls all relevant data and does the filtering and
        counting in code.
        """
        days = (self.queryset.order_by('data_source__year', 'data_source__model', 'day_of_year')
                             .values('data_source__year', 'data_source__model', 'day_of_year', 'pr')
                )
        counts = {}
        for day in days:
            year = counts.setdefault(day['data_source__year'], {})
            model = year.setdefault(day['data_source__model'], {'dry_days': 0,
                                                                'streaks': 0})
            if day['pr'] > 0:
                model['dry_days'] = 0
            else:
                model['dry_days'] += 1
            if model['dry_days'] == 5:
                model['streaks'] += 1
        results = {}
        for yr in counts:
            results[yr] = int_avg([m['streaks'] for m in counts[yr].values()])
        return results


def list_available_indicators():
    """ List the defined class members of this module as the available indicators """
    class_members = inspect.getmembers(sys.modules[__name__], inspect.isclass)
    indicators = [member[1] for member in class_members if member[1].__module__ == __name__]
    return [i.to_dict() for i in indicators]


def indicator_factory(indicator_name):
    """ Return a valid indicator class based on the string provided

    Given a lower case, underscore separated indicator name, return the class associated
    with it. e.g. yearly_frost_days -> indicators.models.YearlyFrostDays
    If no match found, return None

    """
    this_module = sys.modules[__name__]
    class_name = ''.join([s.capitalize() for s in indicator_name.split('_')])
    return getattr(this_module, class_name, None)
