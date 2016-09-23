class IndicatorSerializer(object):
    def to_representation(self, results):
        """ Override this method with indicator specific requirements for serialization """
        return results
