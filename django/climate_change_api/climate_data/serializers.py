from rest_framework import serializers

from climate_data.models import ClimateData


class ClimateDataSerializer(serializers.ModelSerializer):

    class Meta:
        model = ClimateData
