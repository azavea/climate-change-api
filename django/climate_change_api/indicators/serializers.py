from collections import OrderedDict
from datetime import date, timedelta


class IndicatorSerializer(object):
    def to_representation(self, results):
        """ Override this method with indicator specific requirements for serialization """
        return results


class DailyIndicatorSerializer(IndicatorSerializer):

    def to_representation(self, results):

        # Organize the list by day of year
        flat_list = [(d['data_source__year'], d['day_of_year'], d['value'])
                     for d in results if d['value']]
        flat_list.sort(key=lambda (year, day_of_year, value): day_of_year)
        years = set([year for (year, _, _) in flat_list])

        # Use an ordered dictionary to keep response sorted
        output = {year: OrderedDict() for year in years}
        for (year, day_of_year, value) in flat_list:
            day = date(year, 1, 1) + timedelta(days=day_of_year-1)
            output[year][day.isoformat()] = value
        return output
