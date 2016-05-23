from rest_framework import filters, viewsets
from rest_framework_gis.pagination import GeoJsonPagination
from rest_framework_gis.filters import DistanceToPointFilter, InBBoxFilter

from climate_data.filters import ClimateDataFilterSet
from climate_data.models import City, ClimateData, ClimateModel
from climate_data.serializers import (CitySerializer,
                                      ClimateDataSerializer,
                                      ClimateModelSerializer)


class CityViewSet(viewsets.ReadOnlyModelViewSet):

    queryset = City.objects.all()
    serializer_class = CitySerializer
    filter_backends = (DistanceToPointFilter, InBBoxFilter,
                       filters.DjangoFilterBackend, filters.OrderingFilter,)
    filter_fields = ('name', 'admin',)
    ordering_fields = ('name',)
    pagination_class = GeoJsonPagination
    bbox_filter_field = 'geom'
    bbox_filter_include_overlapping = True
    distance_filter_convert_meters = True


class ClimateDataViewSet(viewsets.ReadOnlyModelViewSet):

    queryset = ClimateData.objects.all()
    serializer_class = ClimateDataSerializer
    filter_backends = (filters.DjangoFilterBackend, filters.OrderingFilter,)
    filter_class = ClimateDataFilterSet
    ordering_fields = ('city', 'climate_model', 'year', 'day_of_year', 'tasmin', 'tasmax', 'pr',)


class ClimateModelViewSet(viewsets.ReadOnlyModelViewSet):

    queryset = ClimateModel.objects.all()
    serializer_class = ClimateModelSerializer
    filter_backends = (filters.DjangoFilterBackend, filters.OrderingFilter,)
    filter_fields = ('name',)
    ordering_fields = ('name',)
