
def float_avg(values):
    return float(sum(values)) / len(values)


def int_avg(values):
    return int(round(float_avg(values)))


class IndicatorSerializer(object):
    """ Serialize a django queryset result to a list of dictionaries
    of the form:
        {
            'year': value
        }
    in the case of yearly aggregated indicators, and
        {
            'year': [jan_value, feb_value,...,dec_value]
        }
    in the case of monthly aggregated indicators

    """
    def to_representation(self, results):
        """ Override this method with indicator specific requirements for serialization """
        return results


class YearlyIndicatorSerializer(IndicatorSerializer):
    """
    Reduce year/model query results to yearly average values across models, using floating
    point values.
    """
    def to_representation(self, aggregations):
        results = {}
        for result in aggregations:
            results.setdefault(result['data_source__year'], []).append(result['value'])
        return {yr: float_avg(values) for (yr, values) in results.items()}


class YearlyIntegerIndicatorSerializer(YearlyIndicatorSerializer):
    """
    Reduce year/model query results to yearly average values across models, returning the closest
    integer.
    For use with counting-type indicators for which floating point answers wouldn't make sense.
    """
    def to_representation(self, aggregations):
        results = super(YearlyIntegerIndicatorSerializer, self).to_representation(aggregations)
        return {yr: int(round(val)) for (yr, val) in results.items()}
