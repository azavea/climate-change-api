from collections import OrderedDict
import logging

from django.conf import settings
from django.contrib.gis.geos import Point
from django.core.exceptions import ObjectDoesNotExist
from django.core.exceptions import ValidationError
from django.db import connection, DataError
from django.utils.cache import patch_cache_control

from rest_framework import filters, status, viewsets
from rest_framework.decorators import detail_route, list_route
from rest_framework.exceptions import NotFound
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_gis.pagination import GeoJsonPagination
from rest_framework_gis.filters import InBBoxFilter
from rest_framework.settings import api_settings

from climate_change_api.throttling import (ClimateDataBurstRateThrottle,
                                           ClimateDataSustainedRateThrottle)
from climate_data.caching import (full_url_cache_key_func,
                                  OverridableCacheResponseMixin,
                                  overridable_cache_response)
from climate_data.filters import CityFilterSet, ClimateDataFilterSet
from climate_data.healthchecks import check_data
from climate_data.models import (City,
                                 ClimateData,
                                 ClimateDataYear,
                                 ClimateModel,
                                 Region,
                                 Scenario,
                                 HistoricDateRange)
from climate_data.serializers import (CitySerializer,
                                      CityBoundarySerializer,
                                      ClimateModelSerializer,
                                      ClimateCityScenarioDataSerializer,
                                      RegionDetailSerializer,
                                      RegionListSerializer,
                                      ScenarioSerializer,
                                      HistoricDateRangeSerializer)
from indicators import indicator_factory, list_available_indicators
from .renderers import GeobufRenderer


logger = logging.getLogger(__name__)


DEFAULT_CLIMATE_DATA_MAX_AGE = 60 * 60 * 24 * 30     # 30 days


def climate_data_cache_control(func):
    """Decorator to consistently patch the Cache-Control headers for Climate API endpoints.

    Can be added to any Django Rest Framework view handler method.

    If added to a method with multiple decorators, this one should be called last since it
    invokes the function being decorated.
    """
    def handler(request, *args, **kwargs):
        cache_headers = {
            'max-age': DEFAULT_CLIMATE_DATA_MAX_AGE,
            'private': True
        }
        response = func(request, *args, **kwargs)
        patch_cache_control(response, **cache_headers)
        return response
    return handler


class CityViewSet(OverridableCacheResponseMixin, viewsets.ReadOnlyModelViewSet):
    """Returns a paginated GeoJSON object of the available cities."""

    queryset = City.objects.all().select_related('map_cell')
    serializer_class = CitySerializer
    filter_backends = (InBBoxFilter, filters.DjangoFilterBackend, filters.OrderingFilter,)
    filter_class = CityFilterSet
    ordering_fields = ('name', 'admin', 'population', 'region',)
    pagination_class = GeoJsonPagination
    bbox_filter_field = 'geom'
    bbox_filter_include_overlapping = True
    distance_filter_convert_meters = True

    @list_route(methods=['GET'])
    @overridable_cache_response(key_func=full_url_cache_key_func)
    def nearest(self, request):
        """Given a lat/lon return the nearest city as a GeoJSON feature collection."""
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
        nearest_cities = City.objects.nearest(search_point, limit)

        page = self.paginate_queryset(nearest_cities)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        else:
            serializer = self.get_serializer(nearest_cities, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

    @detail_route(methods=['GET'])
    @overridable_cache_response(key_func=full_url_cache_key_func)
    def boundary(self, request, pk=None):
        """Return the geographical boundary associated with this city as GeoJSON.

        Returns 404 if the city object has no valid boundary.
        """
        city = self.get_object()
        try:
            serializer = CityBoundarySerializer(city.boundary)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except ObjectDoesNotExist:
            return Response(None, status=status.HTTP_404_NOT_FOUND)


class ClimateModelViewSet(OverridableCacheResponseMixin, viewsets.ReadOnlyModelViewSet):

    queryset = ClimateModel.objects.all()
    serializer_class = ClimateModelSerializer
    pagination_class = None
    lookup_field = 'name'
    filter_backends = (filters.DjangoFilterBackend, filters.OrderingFilter,)
    filter_fields = ('name',)
    ordering_fields = ('name',)


class ScenarioViewSet(OverridableCacheResponseMixin, viewsets.ReadOnlyModelViewSet):
    """Filter out the dummy scenario generated by migrations as a placeholder for older data."""

    queryset = Scenario.objects.all()
    serializer_class = ScenarioSerializer
    pagination_class = None
    lookup_field = 'name'
    filter_backends = (filters.DjangoFilterBackend, filters.OrderingFilter,)
    filter_fields = ('name',)
    ordering_fields = ('name',)


class ClimateDataView(APIView):

    throttle_classes = (ClimateDataBurstRateThrottle, ClimateDataSustainedRateThrottle,)

    @overridable_cache_response(key_func=full_url_cache_key_func)
    @climate_data_cache_control
    def get(self, request, *args, **kwargs):
        """Retrieve all of the climate data for a given city and scenario."""
        def filter_variables_list(variables):
            if variables:
                if settings.FEATURE_FLAGS['array_data']:
                    valid_variables = set(ClimateDataYear.VARIABLE_CHOICES)
                else:
                    # TODO: remove this block and feature flag test with task #567
                    valid_variables = set(ClimateData.VARIABLE_CHOICES)
                params_variables = set(variables.split(','))
                return valid_variables.intersection(params_variables)
            else:
                if settings.FEATURE_FLAGS['array_data']:
                    return set(ClimateDataYear.VARIABLE_CHOICES)
                else:
                    # TODO: remove this block and feature flag test with task #567
                    return set(ClimateData.VARIABLE_CHOICES)

        try:
            city = City.objects.get(id=kwargs['city'])
        except (City.DoesNotExist, City.MultipleObjectsReturned):
            raise NotFound(detail='City {} does not exist.'.format(kwargs['city']))

        try:
            scenario = Scenario.objects.get(name=kwargs['scenario'])
        except (Scenario.DoesNotExist, Scenario.MultipleObjectsReturned):
            raise NotFound(detail='Scenario {} does not exist.'.format(kwargs['scenario']))

        if settings.FEATURE_FLAGS['array_data']:
            queryset = ClimateDataYear.objects.filter(
                map_cell=city.map_cell,
                data_source__scenario=scenario
            )
        else:
            # TODO: remove this block and feature flag test with task #567
            queryset = ClimateData.objects.filter(map_cell=city.map_cell,
                                                  data_source__scenario=scenario)

        # Get valid model params list to use in response
        models_param = request.query_params.get('models', None)
        model_list = ClimateModel.objects.all().only('name')
        if models_param:
            model_list = model_list.filter(name__in=models_param.split(','))

        # Get valid variable params list to use in response & serializer context
        variables = request.query_params.get('variables', None)
        cleaned_variables = filter_variables_list(variables)

        # Get valid aggregation param
        AGGREGATION_CHOICES = ('avg', 'min', 'max',)
        aggregation = request.query_params.get('agg', 'avg')
        aggregation = aggregation if aggregation in AGGREGATION_CHOICES else 'avg'

        # Filter on the ClimateData filter set
        data_filter = ClimateDataFilterSet(request.query_params, queryset)

        context = {'variables': cleaned_variables, 'aggregation': aggregation}
        serializer = ClimateCityScenarioDataSerializer(data_filter.qs, context=context)
        return Response(OrderedDict([
            ('city', CitySerializer(city).data),
            ('scenario', scenario.name),
            ('climate_models', [m.name for m in model_list]),
            ('variables', cleaned_variables),
            ('data', serializer.data),
        ]))


class IndicatorListView(APIView):

    @overridable_cache_response()
    def get(self, request, *args, **kwargs):
        """Return the list of available indicators.

        Used to request indicators via /api/climate-data/:city/:scenario/indicator/:name/
        """
        return Response(list_available_indicators())


class IndicatorDetailView(APIView):

    @overridable_cache_response(key_func=full_url_cache_key_func)
    def get(self, request, *args, **kwargs):
        """Return details of specific indicator if found."""
        key = kwargs['indicator']
        IndicatorClass = indicator_factory(key)
        if not IndicatorClass:
            raise NotFound(detail='Indicator {} does not exist.'.format(key))

        return Response(IndicatorClass.to_dict())


class IndicatorDataView(APIView):

    throttle_classes = (ClimateDataBurstRateThrottle, ClimateDataSustainedRateThrottle,)

    @overridable_cache_response(key_func=full_url_cache_key_func)
    @climate_data_cache_control
    def get(self, request, *args, **kwargs):
        """Calculate and return the value of a climate indicator for a given city+scenario."""
        try:
            city = City.objects.get(id=kwargs['city'])
        except (City.DoesNotExist, City.MultipleObjectsReturned):
            raise NotFound(detail='City {} does not exist.'.format(kwargs['city']))

        try:
            scenario = Scenario.objects.get(name=kwargs['scenario'])
        except (Scenario.DoesNotExist, Scenario.MultipleObjectsReturned):
            raise NotFound(detail='Scenario {} does not exist.'.format(kwargs['scenario']))

        # Get valid model params list to use in response
        models_param = request.query_params.get('models', None)
        if models_param:
            model_list = ClimateModel.objects.filter(name__in=models_param.split(','))
        else:
            model_list = ClimateModel.objects.all()

        indicator_key = kwargs['indicator']
        IndicatorClass = indicator_factory(indicator_key)
        if not IndicatorClass:
            raise NotFound(detail='Indicator {} does not exist.'.format(indicator_key))
        try:
            indicator_class = IndicatorClass(city, scenario, parameters=request.query_params)
        except ValidationError as e:
            # If indicator class/params fails validation, return error with help text for
            # as much context as possible.
            return Response(OrderedDict([
                ('error', str(e)),
                ('help', IndicatorClass.init_params_class().to_dict()),
            ]), status=status.HTTP_400_BAD_REQUEST)
        data = indicator_class.calculate()

        return Response(OrderedDict([
            ('city', CitySerializer(city).data),
            ('scenario', scenario.name),
            ('indicator', IndicatorClass.to_dict()),
            ('climate_models', [m.name for m in model_list]),
            ('time_aggregation', indicator_class.params.time_aggregation.value),
            ('units', indicator_class.params.units.value),
            ('data', data),
        ]))


class HistoricDateRangeView(OverridableCacheResponseMixin, viewsets.ReadOnlyModelViewSet):
    """Simple view to see available historic date ranges."""

    queryset = HistoricDateRange.objects.all()
    serializer_class = HistoricDateRangeSerializer
    pagination_class = None
    ordering_fields = ('start_year',)


class RegionListView(OverridableCacheResponseMixin, ListAPIView):
    """Returns a paginated object of all available regions.

    Detail views are GeoJSON, list views are simple dicts.
    """

    queryset = Region.objects.all()
    serializer_class = RegionListSerializer
    filter_backends = (InBBoxFilter, filters.SearchFilter,
                       filters.DjangoFilterBackend, filters.OrderingFilter,)
    filter_fields = ('level1', 'level2',)
    search_fields = ('level1_description', 'level2_description',)
    ordering_fields = ('level1', 'level2',)
    bbox_filter_field = 'geom'
    bbox_filter_include_overlapping = True
    distance_filter_convert_meters = True


class RegionDetailView(APIView):

    renderer_classes = api_settings.DEFAULT_RENDERER_CLASSES + [GeobufRenderer]

    @overridable_cache_response(key_func=full_url_cache_key_func)
    def get(self, request, format=None, *args, **kwargs):
        """Return region as GeoJSON.

        Uses raw query for fetching as GeoJSON because it is much faster to let PostGIS generate
        than Djangonauts serializer.
        """
        region_query = """
        SELECT row_to_json(r) AS region
        FROM (
            SELECT 'Feature' AS type,
                   g.id as id,
                   ST_AsGeoJSON(g.geom)::json AS geometry,
                   row_to_json(p) AS properties
            FROM climate_data_region g
                INNER JOIN (
                    SELECT level1, level1_description,
                           level2, level2_description,
                           id
                    FROM climate_data_region
                ) p ON g.id = p.id AND g.id = %s
        ) AS r;
        """

        key = kwargs['region']

        if request.query_params.get('format') == 'json' or format == 'json':
            # Use raw query to fetch region as GeoJSON
            try:
                with connection.cursor() as cursor:
                    cursor.execute(region_query, [key])
                    region_json = cursor.fetchone()
                    # shouldn't happen with PK, but check anyways
                    if cursor.rowcount > 1:
                        raise NotFound(detail='Multiple responses for region {}.'.format(key))
                    if not region_json or not len(region_json):
                        raise NotFound(detail='Region {} does not exist.'.format(key))
            except DataError:
                raise NotFound(detail='{} is not a valid region ID.'.format(key))

            return Response(region_json[0])
        else:
            # non-JSON format; proceed with using Djangonauts serializer
            try:
                region = Region.objects.get(id=key)
            except (Region.DoesNotExist, Region.MultipleObjectsReturned):
                raise NotFound(detail='Region {} does not exist.'.format(key))

            return Response(RegionDetailSerializer(region).data)

    def finalize_response(self, request, response, *args, **kwargs):
        """Set filename if geobuf."""
        response = super(RegionDetailView, self).finalize_response(request,
                                                                   response,
                                                                   *args,
                                                                   **kwargs)
        if isinstance(response.accepted_renderer, GeobufRenderer):
            region = kwargs['region']
            disposition = 'attachment; filename=region-{}.pbf'.format(region)
            response['content-disposition'] = disposition

        return response


class DataCheckView(APIView):
    """Status check of data imports."""

    def get(self, request, format=None, *args, **kwargs):
        return Response(check_data(),
                        status=status.HTTP_200_OK)
