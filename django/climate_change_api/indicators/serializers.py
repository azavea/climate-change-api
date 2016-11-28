import re
import numpy as np


def float_avg(values):
    return float(sum(values)) / len(values)


class IndicatorSerializer(object):

    AGGREGATION_DEFAULT = ('max', 'min', 'avg',)
    _AGGREGATION_MAP = {
        'avg': float_avg,
        'min': min,
        'max': max,
        'median': np.median,
        'stddev': np.std,
        'stdev': np.std
    }
    _AGGREGATION_CHOICES = _AGGREGATION_MAP.keys()
    _PERCENTILE_REGEX = re.compile('([0-9]?[0-9])th', re.IGNORECASE)

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
         - 'stdev' - Alias to 'stddev'
         - 'XXth' - Percentile. Replace XX with a number between 1-99. This option can be provided
                    multiple times with different values, e.g. ('5th', '95th', '99th',)
        Defaults to ('avg', 'min', 'max',).
        Example: `serializer.to_representation(results, aggregations=('avg', 'stddev', '95th',))`

        """

        def create_percentile_lambda(percentile):
            """ Wrap percentile lambda in function to capture scope of the percentile var """
            return lambda v: np.percentile(v, percentile)

        valid_aggregations = set(self._AGGREGATION_CHOICES)
        kwargs_aggregations = kwargs.get('aggregations', None)
        if kwargs_aggregations:
            kwargs_aggregations = [str(k) for k in kwargs_aggregations]
        else:
            kwargs_aggregations = self.AGGREGATION_DEFAULT

        # Prefilter the list of results here to remove duplicates and invalid values so we don't
        # have to loop the whole results dict later to do so
        aggregations = set(kwargs_aggregations).intersection(valid_aggregations)

        # Add valid percentile agg requests to the aggregation list
        percentiles = [p.strip() for p in kwargs_aggregations
                       if re.match(self._PERCENTILE_REGEX, p.strip())]
        aggregations = aggregations.union(set(percentiles))

        # Add functions for each of the valid requested percentiles to aggregation function map
        aggregation_map = self._AGGREGATION_MAP.copy()
        for p in percentiles:
            match = re.match(self._PERCENTILE_REGEX, p)
            percentile = int(match.groups()[0])
            aggregation_map[p] = create_percentile_lambda(percentile)

        return {key: {agg: aggregation_map[agg](values) for agg in aggregations}
                for (key, values) in results.iteritems()}
