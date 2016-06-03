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


class ClimateModelSerializer(serializers.ModelSerializer):

    class Meta:
        model = ClimateModel
        fields = ('name',)


class ScenarioSerializer(serializers.ModelSerializer):

    class Meta:
        model = Scenario
        fields = ('name', 'description',)
