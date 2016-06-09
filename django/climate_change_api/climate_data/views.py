from collections import OrderedDict
import logging

from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import Point

from rest_framework import filters, generics, status, viewsets
from rest_framework.decorators import list_route
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework_gis.pagination import GeoJsonPagination
from rest_framework_gis.filters import InBBoxFilter

from climate_data.filters import ClimateDataFilterSet
from climate_data.models import City, ClimateData, ClimateModel, Scenario
from climate_data.serializers import (CitySerializer,
                                      ClimateDataSerializer,
                                      ClimateModelSerializer,
                                      ClimateCityScenarioDataSerializer,
                                      ScenarioSerializer)

logger = logging.getLogger(__name__)


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


class ClimateDataList(generics.ListAPIView):
    serializer_class = ClimateDataSerializer
    queryset = ClimateData.objects.all()

    def list(self, request, *args, **kwargs):
        """ Retrieve all of the climate data for a given city and scenario

        URL params:
          - city (int) Required. The city id to limit the values to
          - scenario (str) Required. The scenario name to limit the values to

        GET params:
          - models (str,...,str) Optional. A list of comma separated model names to filter the
            response data by.  If not provided, defaults to all models. The data values in the
            response will be an average of the selected models. e.g. 'CCSM4,GDFL3'
          - variables (str,...,str) Optional. A list of comma separated variables to filter the
            response data by. If not provided, defaults to all variables. e.g. 'tasmax,tasmin'
          - years (str,...,str) Optional. A list of comma separated year ranges to filter the
            response by.  Defaults to all years available. A year range is of the form
            'start[:end]'. These are all valid queries: '2010', '2010:2020', '2010:2020,2030',
            '2010:2020,2030:2040'

        """
        try:
            city = City.objects.get(id=kwargs['city'])
        except (City.DoesNotExist, City.MultipleObjectsReturned) as e:
            raise NotFound(detail='City {} does not exist.'.format(kwargs['city']))

        try:
            scenario = Scenario.objects.get(name=kwargs['scenario'])
        except (Scenario.DoesNotExist, Scenario.MultipleObjectsReturned) as e:
            raise NotFound(detail='Scenario {} does not exist.'.format(kwargs['scenario']))

        queryset = self.get_queryset()
        queryset = queryset.filter(city=city).filter(scenario=scenario)

        # Get valid model params list to use in response
        models_param = request.query_params.get('models', None)
        if models_param:
            model_list = ClimateModel.objects.filter(name__in=models_param.split(','))
        else:
            model_list = ClimateModel.objects.all()

        # Get valid variable params list to use in response & serializer context
        variables = request.query_params.get('variables', None)
        cleaned_variables = self.filter_variables_list(variables)

        # Filter on the ClimateData filter set
        data_filter = ClimateDataFilterSet(request.query_params, queryset)

        context = {'variables': cleaned_variables}
        serializer = ClimateCityScenarioDataSerializer(data_filter.qs, context=context)
        return Response(OrderedDict([
            ('city', CitySerializer(city).data),
            ('scenario', scenario.name),
            ('climate_models', [m.name for m in model_list]),
            ('variables', cleaned_variables),
            ('data', serializer.data),
        ]))

    def filter_variables_list(self, variables):
        if variables:
            valid_variables = set(ClimateData.VARIABLE_CHOICES)
            params_variables = set(variables.split(','))
            return valid_variables.intersection(params_variables)
        else:
            return set(ClimateData.VARIABLE_CHOICES)


class ClimateModelViewSet(viewsets.ReadOnlyModelViewSet):

    queryset = ClimateModel.objects.all()
    serializer_class = ClimateModelSerializer
    lookup_field = 'name'
    filter_backends = (filters.DjangoFilterBackend, filters.OrderingFilter,)
    filter_fields = ('name',)
    ordering_fields = ('name',)


class ScenarioViewSet(viewsets.ReadOnlyModelViewSet):

    # Filter out the dummy scenario generated by migrations as a placeholder for older data
    queryset = Scenario.objects.all()
    serializer_class = ScenarioSerializer
    lookup_field = 'name'
    filter_backends = (filters.DjangoFilterBackend, filters.OrderingFilter,)
    filter_fields = ('name',)
    ordering_fields = ('name',)
