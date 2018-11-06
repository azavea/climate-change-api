from collections import OrderedDict
from itertools import groupby
import logging

from django.db.models import F
from django.db.models.query import QuerySet
from django.db import connection

from rest_framework import serializers
from rest_framework_gis.serializers import GeoFeatureModelSerializer

from climate_data.models import (City,
                                 CityBoundary,
                                 ClimateDataCell,
                                 ClimateDataCityCell,
                                 ClimateDataset,
                                 ClimateDataSource,
                                 ClimateDataYear,
                                 ClimateModel,
                                 Region,
                                 Scenario,
                                 HistoricDateRange)

from indicators.serializers import float_avg

logger = logging.getLogger(__name__)


class HistoricDateRangeSerializer(serializers.ModelSerializer):

    class Meta:
        model = HistoricDateRange
        fields = '__all__'


class ClimateDataCellGeometrySerializer(serializers.ModelSerializer):

    def to_representation(self, obj):
        return OrderedDict([
            ("type", "Point"),
            ("coordinates", [obj.lon, obj.lat])
        ])

    class Meta:
        model = ClimateDataCell


class ClimateDataCellSerializer(serializers.ModelSerializer):

    def to_representation(self, obj):
        return OrderedDict([
            ("type", "Feature"),
            ("geometry", ClimateDataCellGeometrySerializer(obj).data),
            ("properties", {
                "is_coastal": obj.is_coastal
            })
        ])

    class Meta:
        model = ClimateDataCell


class ClimateDataCityCellSerializer(serializers.ModelSerializer):

    def to_representation(self, obj):
        return OrderedDict([
            ("type", "Feature"),
            ("geometry", ClimateDataCellGeometrySerializer(obj.map_cell).data),
            ("properties", {
                "dataset": obj.dataset.name
            })
        ])

    class Meta:
        model = ClimateDataCityCell


class CitySerializer(GeoFeatureModelSerializer):

    proximity = serializers.SerializerMethodField()

    def get_proximity(self, obj):
        return {
            'ocean': obj.is_coastal
        }

    class Meta:
        model = City
        geo_field = 'geom'
        exclude = ('_geog', 'is_coastal')


class CityBoundarySerializer(GeoFeatureModelSerializer):
    class Meta:
        model = CityBoundary
        id_field = False
        geo_field = 'geom'
        exclude = ('id', 'city',)


class ClimateDatasetSerializer(serializers.ModelSerializer):

    models = serializers.SlugRelatedField(
        many=True,
        read_only=True,
        slug_field='name'
    )

    class Meta:
        model = ClimateDataset
        fields = ('name', 'label', 'description', 'url', 'models',)


class ClimateDataSourceSerializer(serializers.ModelSerializer):

    class Meta:
        model = ClimateDataSource


class ClimateMapCellScenarioDataSerializer(serializers.BaseSerializer):
    """Read-only custom serializer to generate the data object for the ClimateDataList view.

    Since we will be combining multiple ClimateDataYear instances into a single unified output,
    this serializer takes a ClimateDataYear queryset and does not use the many=True argument,
    but does require the serializer `context` kwarg with a key 'variables'.

    :param instance Queryset A ClimateDataYear Queryset
        It should already be filtered on ClimateDataCell and Scenario before
        being passed to the serializer
    :param context Dict
        Provide key 'variables' with an iterable subset of ClimateDataYear.VARIABLE_CHOICES to
        filter the output.
        Provide key 'aggregation' with one of ('min', 'max', 'avg') to aggregate the data values
        across models. Default is 'avg'.
    """

    def __init__(self, instance=None, **kwargs):
        super(ClimateMapCellScenarioDataSerializer, self).__init__(instance, **kwargs)
        if self._context.get('variables', None) is None:
            self._context['variables'] = ClimateDataYear.VARIABLE_CHOICES
        if self._context.get('aggregation', None) is None:
            self._context['aggregation'] = 'avg'

    def to_representation(self, queryset):
        aggregation_map = {
            'avg': float_avg,
            'min': min,
            'max': max
        }
        """Serialize queryset to the expected python object format."""
        assert isinstance(queryset, QuerySet), (
            'ClimateMapCellScenarioDataSerializer must be given a queryset')

        aggregation = self._context['aggregation']

        # default to averaging
        aggregation_func = aggregation_map.get(aggregation, float_avg)

        queryset = queryset.annotate(year=F('data_source__year'), model=F('data_source__model'))
        queryset = queryset.order_by('year')

        query = str(queryset.query)
        cursor = connection.cursor()
        cursor.execute(query)

        output = {}
        columns = [col[0] for col in cursor.description]
        results = (dict(zip(columns, row)) for row in cursor.fetchall())
        for year, year_collection in groupby(results, lambda r: r['year']):
            year_collection = list(year_collection)
            output[year] = {var: [None] * 366 for var in self._context['variables']}
            for variable in self._context['variables']:
                year_results = [r[variable] for r in year_collection]
                for day, var_day in enumerate(zip(*year_results)):
                    values = [val for val in var_day if val is not None]
                    output[year][variable][day] = aggregation_func(values)

        return output

    def to_internal_value(self, data):
        raise NotImplementedError('ClimateMapCellScenarioDataSerializer is read only!')

    def create(self, validated_data):
        raise NotImplementedError('ClimateMapCellScenarioDataSerializer is read only!')

    def update(self, instance, validated_data):
        raise NotImplementedError('ClimateMapCellScenarioDataSerializer is read only!')


class ClimateModelSerializer(serializers.ModelSerializer):

    datasets = serializers.SlugRelatedField(
        many=True,
        read_only=True,
        slug_field='name'
    )

    class Meta:
        model = ClimateModel
        exclude = ('id',)


class RegionDetailSerializer(GeoFeatureModelSerializer):

    class Meta:
        model = Region
        geo_field = 'geom'
        # explicitly set auto_bbox to False and bbox_geo_field to None (the default for both)
        # because our JSON renderer in the view does not respect bounding boxes
        auto_bbox = False
        bbox_geo_field = None


class RegionListSerializer(serializers.ModelSerializer):

    class Meta:
        model = Region
        exclude = ('geom',)


class ScenarioSerializer(serializers.ModelSerializer):

    class Meta:
        model = Scenario
        exclude = ('id',)
