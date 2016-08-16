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

    @property
    def key(self):
        return 'INDICATOR -- override in subclass'

    @property
    def label(self):
        return 'Generic Indicator -- override in subclass'

    @property
    def description(self):
        return 'Generic description -- override in subclass'

    def filter_objects(self):
        """ A subclass can override this to further filter the dataset before calling calculate """
        return self.queryset

    def calculate(self):
        """ Calculate the indicator """
        raise NotImplementedError('Subclasses must implement calculate()')


class YearlyAverageMaxTemperature(Indicator):

    @property
    def key(self):
        return 'YEARLY_AVG_MAX_TEMP'

    @property
    def label(self):
        return 'Yearly Average Max Temperature'

    @property
    def description(self):
        return ''

    def calculate(self):
        return {}


INDICATOR_MAP = {
    'yearly_avg_max_temp': YearlyAverageMaxTemperature,
}
