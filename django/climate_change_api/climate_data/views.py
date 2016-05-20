from rest_framework import filters, viewsets

from climate_data.models import City, ClimateData, ClimateModel
from climate_data.serializers import (CitySerializer,
                                      ClimateDataSerializer,
                                      ClimateModelSerializer)


class CityViewSet(viewsets.ReadOnlyModelViewSet):

    queryset = City.objects.all()
    serializer_class = CitySerializer
    filter_backends = (filters.DjangoFilterBackend, filters.OrderingFilter,)
    ordering_fields = ('name',)


class ClimateDataViewSet(viewsets.ReadOnlyModelViewSet):

    queryset = ClimateData.objects.all()
    serializer_class = ClimateDataSerializer
    filter_backends = (filters.DjangoFilterBackend, filters.OrderingFilter,)
    ordering_fields = ('city', 'climate_model', 'year', 'day_of_year', 'tasmin', 'tasmax', 'pr',)


class ClimateModelViewSet(viewsets.ReadOnlyModelViewSet):

    queryset = ClimateModel.objects.all()
    serializer_class = ClimateModelSerializer
    filter_backends = (filters.DjangoFilterBackend, filters.OrderingFilter,)
    ordering_fields = ('name',)
