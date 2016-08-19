
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

    def to_representation(self, results):
        output = {}
        for result in results:
            output[result['data_source__year']] = result['value']
        return output
