
class IndicatorSerializer(object):

    def to_representation(self, results):
        return results


class YearlyIndicatorSerializer(IndicatorSerializer):

    def to_representation(self, results):
        output = {}
        for result in results:
            output[result['data_source__year']] = result['value']
        return output
