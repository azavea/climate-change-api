from rest_framework import serializers

from climate_data.models import City, ClimateData, ClimateModel


class CitySerializer(serializers.ModelSerializer):

    class Meta:
        model = City
        fields = ()


class ClimateDataSerializer(serializers.ModelSerializer):

    city = serializers.HyperlinkedRelatedField(read_only=True, view_name='city-detail')
    climate_model = serializers.SlugRelatedField(read_only=True, slug_field='name')

    class Meta:
        model = ClimateData


class ClimateModelSerializer(serializers.ModelSerializer):

    class Meta:
        model = ClimateModel
        fields = ('name',)
