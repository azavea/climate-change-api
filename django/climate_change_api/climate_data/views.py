from rest_framework import filters, viewsets

from climate_data.models import ClimateData
from climate_data.serializers import ClimateDataSerializer


class ClimateDataViewSet(viewsets.ReadOnlyModelViewSet):

    queryset = ClimateData.objects.all()
    serializer_class = ClimateDataSerializer
    filter_backends = (filters.DjangoFilterBackend, filters.OrderingFilter,)
    ordering_fields = ('city', 'climate_model', 'year', 'day_of_year', 'tasmin', 'tasmax', 'pr',)
