from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import Point

from rest_framework import filters, status, viewsets
from rest_framework.decorators import list_route
from rest_framework.response import Response
from rest_framework_gis.pagination import GeoJsonPagination
from rest_framework_gis.filters import InBBoxFilter

from climate_data.filters import ClimateDataFilterSet
from climate_data.models import City, ClimateData, ClimateModel
from climate_data.serializers import (CitySerializer,
                                      ClimateDataSerializer,
                                      ClimateModelSerializer)


class CityViewSet(viewsets.ReadOnlyModelViewSet):

    queryset = City.objects.all()
    serializer_class = CitySerializer
    filter_backends = (InBBoxFilter,
                       filters.DjangoFilterBackend, filters.OrderingFilter,)
    filter_fields = ('name', 'admin',)
    ordering_fields = ('name',)
    pagination_class = GeoJsonPagination
    bbox_filter_field = 'geom'
    bbox_filter_include_overlapping = True
    distance_filter_convert_meters = True

    @list_route(methods=['GET'])
    def nearest(self, request):
        """ Given a lat/lon return the nearest city as a GeoJSON feature collection

        GET params:
          - lat (float) Required. The latitude to search at.
          - lon (float) Required. The longitude to search at.
          - limit (int) The number of results to return. Default: 1.

        """
        try:
            lat = float(request.query_params.get('lat', None))
        except (TypeError, ValueError):
            return Response({'error': 'lat must be a float'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            lon = float(request.query_params.get('lon', None))
        except (TypeError, ValueError):
            return Response({'error': 'lon must be a float'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            limit = int(request.query_params.get('limit', 1))
        except (TypeError, ValueError):
            return Response({'error': 'limit must be an int'}, status=status.HTTP_400_BAD_REQUEST)
        if limit < 1:
            return Response({'error': 'limit must be greater than zero'},
                            status=status.HTTP_400_BAD_REQUEST)

        search_point = Point(lon, lat, srid=4326)
        nearest_cities = (City.objects.annotate(distance=Distance('geom', search_point))
                                      .order_by('distance')[:limit])
        page = self.paginate_queryset(nearest_cities)
        serializer = self.get_serializer(nearest_cities, many=True)
        if page is not None:
            return self.get_paginated_response(serializer.data)
        else:
            return Response(serializer.data, status=status.HTTP_200_OK)


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
