import numpy as np

def float_avg(values):
    return float(sum(values)) / len(values)

def percentile_95(values):
    return np.percentile(values, 95)

def percentile_99(values):
    return np.percentile(values, 99)


class IndicatorSerializer(object):

    AGGREGATION_MAP = {
        'avg': float_avg,
        'min': min,
        'max': max,
        'median': np.median,
        'stddev': np.std,
        '95th': percentile_95,
        '99th': percentile_99
    }
    AGGREGATION_CHOICES = AGGREGATION_MAP.keys()
    AGGREGATION_DEFAULT = ('max', 'min', 'avg',)

    def to_representation(self, results, **kwargs):
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

        Passing a 'aggregations' kwarg allows the user to customize the aggregations returned in
        the result dict. This aggregations parameter should be an iterable of string aggregation
        types, of which the following are supported:
         - 'avg' - Average of the values
         - 'min' - Absolute minimum of the values
         - 'max' - Absolute max of the values
         - 'median' - Median of the values
         - 'stddev' - Standard deviation of the values
         - '95th' - 95th percentile
         - '99th' - 99th percentile
        Defaults to ('avg', 'min', 'max',).
        Example: `serializer.to_representation(results, aggregations=('avg', 'stddev', '95th',))`

        """
        valid_aggregations = set(self.AGGREGATION_CHOICES)
        kwargs_aggregations = kwargs.get('aggregations', None)
        if not kwargs_aggregations:
            kwargs_aggregations = self.AGGREGATION_DEFAULT
        aggregations = set(kwargs_aggregations).intersection(valid_aggregations)

        return {key: {agg: self.AGGREGATION_MAP[agg](values) for agg in aggregations}
                for (key, values) in results.iteritems()}
