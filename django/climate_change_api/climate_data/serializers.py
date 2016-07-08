import django.db.models
from django.db.models.query import QuerySet

from rest_framework import serializers
from rest_framework_gis.serializers import GeoFeatureModelSerializer

from climate_data.models import City, ClimateData, ClimateModel, Scenario


class CitySerializer(GeoFeatureModelSerializer):

    class Meta:
        model = City
        geo_field = 'geom'


class ClimateDataSerializer(serializers.ModelSerializer):

    city = serializers.HyperlinkedRelatedField(read_only=True, view_name='city-detail')
    climate_model = serializers.SlugRelatedField(read_only=True, slug_field='name')
    scenario = serializers.SlugRelatedField(read_only=True, slug_field='name')

    class Meta:
        model = ClimateData


class ClimateCityScenarioDataSerializer(serializers.BaseSerializer):
    """ Read-only custom serializer to generate the data object for the ClimateDataList view

    Since we will be combining multiple ClimateData model instances into a single unified
    output, this serializer takes a ClimateData queryset and does not use the many=True argument,
    but does require the serializer `context` kwarg with a key 'variables'

    :param instance Queryset A ClimateData Queryset
        It should already be filtered on City and Scenario before being passed to the serializer
    :param context Dict
        Provide key 'variables' with an iterable subset of ClimateData.VARIABLE_CHOICES to filter
        the output.
        Provide key 'aggregation' with one of ('min', 'max', 'avg') to aggregate the data values
        across models. Default is 'avg'.

    """
    def __init__(self, instance=None, **kwargs):
        super(ClimateCityScenarioDataSerializer, self).__init__(instance, **kwargs)
        if self._context.get('variables', None) is None:
            self._context['variables'] = ClimateData.VARIABLE_CHOICES
        if self._context.get('aggregation', None) is None:
            self._context['aggregation'] = 'avg'

    def to_representation(self, queryset):
        """ Serialize queryset to the expected python object format

        The DB query should be roughly equivalent to:
            SELECT year, day_of_year, avg(tasmin) as tasmin, avg(tasmax) as tasmax, avg(pr) as pr
            FROM climate_data_climatedata
            WHERE scenario_id = 1 and city_id = 1
            GROUP BY year, day_of_year
            ORDER BY year, day_of_year;

        """
        assert isinstance(queryset, QuerySet), 'ClimateCityScenarioDataSerializer must be given a queryset'

        aggregation = self._context['aggregation']
        aggregation_function = getattr(django.db.models, aggregation.capitalize())

        aggregations = {variable: aggregation_function(variable)
                        for variable in self._context['variables']}
        results = queryset.values('year', 'day_of_year').annotate(**aggregations)
        output = {}
        for result in results:
            year = result['year']
            day_of_year = result['day_of_year']
            if year not in output:
                output[year] = {}
            year_data = output[year]
            for variable in self._context['variables']:
                if variable not in year_data:
                    year_data[variable] = [None] * 366
                year_data[variable][day_of_year - 1] = result[variable]
        return output

    def to_internal_value(self, data):
        raise NotImplementedError('ClimateCityScenarioDataSerializer is read only!')

    def create(self, validated_data):
        raise NotImplementedError('ClimateCityScenarioDataSerializer is read only!')

    def update(self, instance, validated_data):
        raise NotImplementedError('ClimateCityScenarioDataSerializer is read only!')


class ClimateModelSerializer(serializers.ModelSerializer):

    class Meta:
        model = ClimateModel
        fields = ('name',)


class ScenarioSerializer(serializers.ModelSerializer):

    class Meta:
        model = Scenario
        fields = ('name', 'description',)
