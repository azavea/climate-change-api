from collections import OrderedDict
from datetime import date, timedelta


class IndicatorSerializer(object):
    def to_representation(self, results):
        """ Override this method with indicator specific requirements for serialization """
        return results


class DailyIndicatorSerializer(IndicatorSerializer):

    def to_representation(self, results):
        # Convert the timeseries data into a more easily digestible tuple format
        # The list is already sorted, so we can just maintain the original order
        tuple_list = ((d['data_source__year'], d['day_of_year'], d['value'])
                     for d in results if d['value'])

        # Use ordered dicts to guarantee output order
        output = OrderedDict()
        for (year, day_of_year, value) in tuple_list:
            if year not in output:
                output[year] = OrderedDict()

            # Convert year and day_of_year to a Python date object
            day = date(year, 1, 1) + timedelta(days=day_of_year-1)
            output[year][day.isoformat()] = value
        return output
