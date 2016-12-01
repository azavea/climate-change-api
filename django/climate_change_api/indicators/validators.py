from rest_framework.exceptions import ValidationError

PERCENTILES = set([1, 5, 95, 99])


##########################
# Indicator validators

class PercentileValidatorMixin(object):
        def validate(self):
            if int(self.parameters['percentile']) not in PERCENTILES:
                    raise ValidationError("Parameter percentile must be one of {}"
                                          .format(", ".join(str(x) for x in sorted(PERCENTILES))))
