def float_avg(values):
    return float(sum(values)) / len(values)


class IndicatorSerializer(object):
    def to_representation(self, results):
        """ Simplify the full list of collated data points to a constant summary

        Given the results of `aggregate`, should produce a dictionary of the form:
        {
            'time_repr': {'avg': value, 'min': value, 'max': value}
        }

        Where 'time_repr' is the date in a hyphen-deliminated ISO-8601 format for
        the appropriate aggregation level. Specifically, one of the following:
        * YYYY for yearly data
        * YYYY-MM for monthly data
        * YYYY-MM-DD for daily data

        _Do not_ use YYYYMMDD

        For example, a yearly indicator could be presented as:
        {
            '2050': {'avg': value, 'min': value, 'max': value}
        }

        And a monthly indicator as:
        {
            '2050-03': {'avg': value, 'min': value, 'max': value}
        }

        """
        return {key: {'avg': float_avg(values),
                      'min': min(values),
                      'max': max(values)}
                for (key, values) in results.iteritems()}
