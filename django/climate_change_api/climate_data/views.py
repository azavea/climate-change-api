from collections import OrderedDict
import logging

from django.contrib.gis.geos import Point
from django.core.exceptions import ObjectDoesNotExist
from django.core.exceptions import ValidationError
from django.db import connection, DataError
from django.utils.cache import patch_cache_control

from rest_framework import filters, status, viewsets
from rest_framework.decorators import detail_route, list_route
from rest_framework.exceptions import NotFound, ParseError
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
                                 ClimateDataset,
                                 ClimateDataCell,
                                 ClimateDataCityCell,
                                 ClimateDataYear,
                                 ClimateModel,
                                 HistoricDateRange,
                                 Region,
                                 Scenario)
from climate_data.serializers import (CitySerializer,
                                      CityBoundarySerializer,
                                      ClimateDatasetSerializer,
                                      ClimateDataCellSerializer,
                                      ClimateDataCityCellSerializer,
                                      ClimateModelSerializer,
                                      ClimateMapCellScenarioDataSerializer,
                                      RegionDetailSerializer,
                                      RegionListSerializer,
                                      ScenarioSerializer,
                                      HistoricDateRangeSerializer)
from indicators import indicator_factory, list_available_indicators
from .renderers import GeobufRenderer


logger = logging.getLogger(__name__)


DEFAULT_CLIMATE_DATA_MAX_AGE = 60 * 60 * 24 * 30     # 30 days


def climate_data_cache_control(func):
    """Consistently patch the Cache-Control headers for Climate API endpoints with decorator.

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


class ClimateParamsValidationMixin(object):
    """Provides methods with validate request params for climate requests.

    Supported:
    - URL kwarg scenario -> Scenario
    - param agg -> valid 'agg', default set if none provided
    - param dataset -> ClimateDataset
    - param models -> ['model_names']
    - param variables -> ['variable_names']

    """

    def validate_kwarg_scenario(self, **kwargs):
        """Return valid Scenario from url kwargs.

        Raise .DoesNotExist or MultipleObjectsReturned if exactly one scenario is not found.

        """
        try:
            return Scenario.objects.get(name=kwargs['scenario'])
        except (Scenario.DoesNotExist, Scenario.MultipleObjectsReturned):
            raise NotFound(detail='Scenario {} does not exist.'.format(kwargs['scenario']))

    def validate_param_agg(self, request, default='avg'):
        """Return validated agg string param, must be one of 'avg', 'min', 'max'.

        Raises ParseError if value provided and its not one of the valid AGGREGATION_CHOICES.

        """
        AGGREGATION_CHOICES = ('avg', 'min', 'max',)
        aggregation = request.query_params.get('agg', default)
        if aggregation in AGGREGATION_CHOICES:
            return aggregation
        else:
            raise ParseError('Param agg must be one of {}'.format(AGGREGATION_CHOICES))

    def validate_param_dataset(self, request, default='NEX-GDDP'):
        """Return valid ClimateDataset from GET param.

        Raise DRF ParseError if dataset invalid or not found

        """
        DATASET_CHOICES = set(ClimateDataset.datasets())
        dataset_param = request.query_params.get('dataset', default)
        if dataset_param not in DATASET_CHOICES:
            raise ParseError(detail='Dataset {} does not exist. Choose one of {}.'
                                    .format(dataset_param, DATASET_CHOICES))
        return ClimateDataset.objects.get(name=dataset_param)

    def validate_param_models(self, request, dataset):
        """Validate and return cleaned models list as array of string values."""
        models_param = request.query_params.get('models', None)
        if models_param:
            models_param_list = models_param.split(',')
            model_list = (dataset.models.filter(name__in=models_param_list)
                                        .values_list('name', flat=True))
            invalid_models = set(models_param_list) - set(model_list)
            if invalid_models:
                raise ParseError('Dataset %s has no data for model(s): %s'
                                 % (dataset.name, ','.join(invalid_models)))
        else:
            # no model filter; use all available for dataset
            model_list = dataset.models.all().values_list('name', flat=True)
        return model_list

    def validate_param_variables(self, request):
        """Validate and return cleaned variable list as array of string values."""
        def filter_variables_list(variables):
            if variables:
                valid_variables = set(ClimateDataYear.VARIABLE_CHOICES)
                params_variables = set(variables.split(','))
                return valid_variables.intersection(params_variables)
            else:
                return set(ClimateDataYear.VARIABLE_CHOICES)

        # Get valid variable params list to use in response & serializer context
        variables = request.query_params.get('variables', None)
        return filter_variables_list(variables)


class CityViewSet(OverridableCacheResponseMixin, viewsets.ReadOnlyModelViewSet):
    """Returns a paginated GeoJSON object of the available cities."""

    queryset = City.objects.all()
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

    @detail_route(methods=['GET'])
    @overridable_cache_response(key_func=full_url_cache_key_func)
    def datasets(self, request, pk=None):
        """Return the names of the datasets assocated with a city.

        Returns 404 if the city object has no valid map cells.
        """
        city = self.get_object()
        return Response(city.datasets, status=status.HTTP_200_OK)


class CityMapCellListView(APIView):

    @overridable_cache_response(key_func=full_url_cache_key_func)
    def get(self, request, *args, **kwargs):
        """Return the map cells associated with a city.

        Returns 404 if the city object has no valid map cells.
        """
        map_cells = ClimateDataCityCell.objects.filter(city_id=kwargs['city'])
        if len(map_cells) == 0:
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
        response = [ClimateDataCityCellSerializer(map_cell).data for map_cell in map_cells]
        return Response(response, status=status.HTTP_200_OK)


class LatLonMapCellListView(APIView):

    @overridable_cache_response(key_func=full_url_cache_key_func)
    def get(self, request, *args, **kwargs):
        """Return the map cells associated with a Lat/Lon point.

        Returns 404 if the point has no valid map cells.
        """
        data = []
        for dataset in ClimateDataset.objects.all():
            try:
                map_cell = ClimateDataCell.objects.map_cell_for_lat_lon(
                    float(kwargs['lat']),
                    float(kwargs['lon']),
                    dataset,
                )
                serializer = ClimateDataCellSerializer(map_cell, context={
                    'dataset': dataset
                })
                data.append(serializer.data)
            except ClimateDataCell.DoesNotExist:
                pass

        if len(data) == 0:
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)

        return Response(data, status=status.HTTP_200_OK)


class CityMapCellDatasetDetailView(APIView):

    @overridable_cache_response(key_func=full_url_cache_key_func)
    def get(self, request, *args, **kwargs):
        """Return the detail of a map cell assocated with a city and dataset.

        Returns 404 if the city object has no valid map cells.
        """
        try:
            map_cell = ClimateDataCityCell.objects.get(city_id=kwargs['city'],
                                                       dataset__name=kwargs['dataset'])
            response = ClimateDataCityCellSerializer(map_cell).data
            return Response(response, status=status.HTTP_200_OK)
        except ClimateDataCityCell.DoesNotExist:
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)


class ClimateDatasetViewSet(OverridableCacheResponseMixin, viewsets.ReadOnlyModelViewSet):

    queryset = ClimateDataset.objects.all()
    serializer_class = ClimateDatasetSerializer
    pagination_class = None
    lookup_field = 'name'
    filter_backends = (filters.DjangoFilterBackend, filters.OrderingFilter,)
    filter_fields = ('name',)
    ordering_fields = ('name',)
    ordering = ('name',)


class ClimateModelViewSet(OverridableCacheResponseMixin, viewsets.ReadOnlyModelViewSet):

    queryset = ClimateModel.objects.all()
    serializer_class = ClimateModelSerializer
    pagination_class = None
    lookup_field = 'name'
    filter_backends = (filters.DjangoFilterBackend, filters.OrderingFilter,)
    filter_fields = ('name',)
    ordering_fields = ('name',)
    ordering = ('name',)


class ScenarioViewSet(OverridableCacheResponseMixin, viewsets.ReadOnlyModelViewSet):
    """Filter out the dummy scenario generated by migrations as a placeholder for older data."""

    queryset = Scenario.objects.all()
    serializer_class = ScenarioSerializer
    pagination_class = None
    lookup_field = 'name'
    filter_backends = (filters.DjangoFilterBackend, filters.OrderingFilter,)
    filter_fields = ('name',)
    ordering_fields = ('name',)
    ordering = ('name',)


class ClimateDataMixin(object):

    def get_data(self, request, dataset, map_cell, scenario, kwargs):
        aggregation = self.validate_param_agg(request, default='avg')
        model_list = self.validate_param_models(request, dataset)
        variables = self.validate_param_variables(request)

        serializer = self.serializer_for(request, dataset, map_cell, scenario,
                                         variables, aggregation)

        return OrderedDict([
            ('dataset', dataset.name),
            ('scenario', scenario.name),
            ('climate_models', list(model_list)),
            ('variables', variables),
            ('data', serializer.data),
        ])

    def serializer_for(self, request, dataset, map_cell, scenario, variables, aggregation):

        try:
            queryset = ClimateDataYear.objects.filter(
                map_cell=map_cell,
                data_source__scenario=scenario
            )
        except ClimateDataCell.DoesNotExist:
            raise ParseError(detail='No data available for {} dataset at this location'
                                    .format(dataset.name))

        # Filter on the ClimateData filter set
        data_filter = ClimateDataFilterSet(request.query_params, queryset)

        context = {'variables': variables, 'aggregation': aggregation}
        return ClimateMapCellScenarioDataSerializer(data_filter.qs, context=context)


class CityCellAPIView(ClimateParamsValidationMixin, APIView):

    throttle_classes = (ClimateDataBurstRateThrottle, ClimateDataSustainedRateThrottle,)

    @overridable_cache_response(key_func=full_url_cache_key_func)
    @climate_data_cache_control
    def get(self, request, *args, **kwargs):
        scenario = self.validate_kwarg_scenario(**kwargs)
        dataset = self.validate_param_dataset(request, default=ClimateDataset.Datasets.NEX_GDDP)
        city, map_cell = self.get_map_cell(dataset, kwargs)

        response_data = OrderedDict([('city', CitySerializer(city).data)])
        response_data.update(self.get_data(request, dataset, map_cell, scenario, kwargs))
        return Response(response_data)

    def get_map_cell(self, dataset, kwargs):
        try:
            city = City.objects.get(id=kwargs['city'])
        except (City.DoesNotExist, City.MultipleObjectsReturned):
            raise NotFound(detail='City {} does not exist.'.format(kwargs['city']))
        return city, city.get_map_cell(dataset)


class LatLonCellAPIView(ClimateParamsValidationMixin, APIView):

    throttle_classes = (ClimateDataBurstRateThrottle, ClimateDataSustainedRateThrottle,)

    @overridable_cache_response(key_func=full_url_cache_key_func)
    @climate_data_cache_control
    def get(self, request, *args, **kwargs):
        scenario = self.validate_kwarg_scenario(**kwargs)
        dataset = self.validate_param_dataset(request, default=ClimateDataset.Datasets.NEX_GDDP)
        map_cell = self.get_map_cell(dataset, kwargs)

        response_data = OrderedDict([
            ('feature', ClimateDataCellSerializer(map_cell).data),
        ])
        response_data.update(self.get_data(request, dataset, map_cell, scenario, kwargs))
        return Response(response_data)

    def get_map_cell(self, dataset, kwargs):
        try:
            return ClimateDataCell.objects.map_cell_for_lat_lon(float(kwargs['lat']),
                                                                float(kwargs['lon']),
                                                                dataset)
        except ClimateDataCell.DoesNotExist:
            raise NotFound(detail='No {} data available for point ({}, {})'
                                  .format(dataset.name, kwargs['lat'], kwargs['lon']))


class ClimateDataForCityView(ClimateDataMixin, CityCellAPIView):
    pass


class ClimateDataForLatLonView(ClimateDataMixin, LatLonCellAPIView):
    pass


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


class IndicatorDataMixin(object):

    def get_data(self, request, dataset, map_cell, scenario, kwargs):
        model_list = self.validate_param_models(request, dataset)

        indicator_key = kwargs['indicator']
        IndicatorClass = indicator_factory(indicator_key)
        if not IndicatorClass:
            raise NotFound(detail='Indicator {} does not exist.'.format(indicator_key))
        try:
            indicator_class = IndicatorClass(map_cell, scenario, parameters=request.query_params)
            data = indicator_class.calculate()
        except ValidationError as e:
            # If indicator class/params fails validation, return error with help text for
            # as much context as possible.
            return Response(OrderedDict([
                ('error', str(e)),
                ('help', IndicatorClass.init_params_class().to_dict()),
            ]), status=status.HTTP_400_BAD_REQUEST)

        return OrderedDict([
            ('dataset', dataset.name),
            ('scenario', scenario.name),
            ('indicator', IndicatorClass.to_dict()),
            ('climate_models', list(model_list)),
            ('time_aggregation', indicator_class.params.time_aggregation.value),
            ('units', indicator_class.params.units.value),
            ('data', data),
        ])


class IndicatorDataForCityView(IndicatorDataMixin, CityCellAPIView):
    pass


class IndicatorDataForLatLonView(IndicatorDataMixin, LatLonCellAPIView):
    pass


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
