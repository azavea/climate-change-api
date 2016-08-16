from django.db.models import Avg

from climate_data.models import ClimateData

class Indicator(object):

    def __init__(self, city, scenario, models=None, years=None):
        if not city:
            raise ValueError('Indicator constructor requires a city instance')
        if not scenario:
            raise ValueError('Indicator constructor requires a scenario instance')

        self.models = self._validate_models(models)
        self.years = self._validate_years(years)

        self.queryset = (ClimateData.objects.filter(map_cell=city.map_cell)
                                            .filter(data_source__scenario=scenario))
        self.queryset = self.filter_objects()

    def _validate_models(self, model_list):
        return model_list

    def _validate_years(self, year_list):
        return year_list

    def filter_objects(self):
        """ A subclass can override this to further filter the dataset before calling calculate """
        return self.queryset

    def calculate(self):
        """ Calculate the indicator

        This method should use self.queryset to calculate the indicator returning a dict
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
        raise NotImplementedError('Subclasses must implement calculate()')


class YearlyIndicator(Indicator):

    def serialize(self, results, varname):
        output = {}
        for result in results:
            output[result['data_source__year']] = result[varname]
        return output


class YearlyAverageMaxTemperature(YearlyIndicator):

    def calculate(self):
        results = self.queryset.values('data_source__year').annotate(tasmax=Avg('tasmax'))
        return self.serialize(results, 'tasmax')


class YearlyAverageMinTemperature(YearlyIndicator):

    def calculate(self):
        results = self.queryset.values('data_source__year').annotate(tasmin=Avg('tasmin'))
        return self.serialize(results, 'tasmin')


INDICATOR_MAP = {
    'yearly_avg_max_temp': YearlyAverageMaxTemperature,
    'yearly_avg_min_temp': YearlyAverageMinTemperature,
}
