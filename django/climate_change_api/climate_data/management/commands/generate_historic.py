import logging
import gc
import numpy as np

from django.core.management.base import BaseCommand

from climate_data.models import (ClimateData, ClimateDataCell, HistoricAverageClimateData,
                                 ClimateDataBaseline, ClimateModel)
from django.db.models import Avg, F

logger = logging.getLogger('climate_data')

CITY_URL = 'https://{domain}/api/city/?format=json'

RAWDATA_URL = 'https://{domain}/api/climate-data/{city}/historical/'
VARIABLES = ['tasmin', 'tasmax', 'pr']
MODELS = ClimateModel.objects.all()
CHUNKSIZE = 10


def row_get_value(row, value):
    try:
        return row.getattr(value)
    except AttributeError:
        return row[value]


def queryset_iterator(queryset, chunksize=1000, pk='pk'):
    """
    Iterate over a Django Queryset ordered by the primary key

    Code from https://djangosnippets.org/snippets/1949/

    Splits a Django query set into chunks to alleviate memory consumption problems and allow for
    smoother, less front-heavy operation with a generator workflow.

    By default Django querysets read all data immediately, which when dealing with millions of rows
    can be prohibitively expensive (Read: Causes the script to crash). This helps with workflow
    smoothness when used in conjunction with a generator-friendly insert function.
    """
    i = 0
    try:
        last_pk = row_get_value(queryset.order_by('-pk')[0], pk)
    except IndexError:
        # The queryset has no rows to return
        return

    queryset = queryset.order_by('pk')
    while i < last_pk:
        for row in queryset.filter(pk__gt=pk)[:chunksize]:
            i = row_get_value(row, pk)
            yield row
        gc.collect()


def import_baselines(queryset):
    """
    Streams a series of baselines to bulk_create, using the chunk size parameter to help with memory
    usage. Normally Django would attempt to insert all objects in one step, no matter how many,
    which front-loads task operation and leads to memory problems when inserting a significant
    number of objects at once.
    """
    logger.info("Importing baselines")
    baselines = generate_baselines(queryset)

    ClimateDataBaseline.objects.bulk_create(baselines, CHUNKSIZE)


def generate_baselines(queryset):
    """
    Generates baselines for cells that are represented by the queryset but do not have any baseline
    objects of their own.
    """
    cells = ClimateDataCell.objects.filter(baseline__isnull=True,
                                           id__in=queryset.values('map_cell'))
    print cells.query
    for cell in queryset_iterator(cells, CHUNKSIZE):
        logger.info("Importing baselines for cell (%f,%f)", cell.lat, cell.lon)
        data = queryset.filter(map_cell=cell)

        precip_99ps = [np.percentile(data.filter(data_source__model=model)
                                         .values_list('pr', flat=True), 99)
                       for model in MODELS]

        yield ClimateDataBaseline(
            map_cell=cell,
            precip_99p=np.mean(precip_99ps)
        )


def import_averages(queryset):
    logger.info("Importing averages")

    records = generate_averages(queryset)

    HistoricAverageClimateData.objects.bulk_create(records, CHUNKSIZE)


def generate_averages(queryset):
    averages = (queryset
                .values('map_cell', 'day_of_year')
                .exclude(id__in=queryset.filter(map_cell__historic_average__day_of_year=F('day_of_year')))
                .annotate(**{var: Avg(var) for var in VARIABLES}))
    print averages.query
    for row in queryset_iterator(averages, CHUNKSIZE):
        print row
        yield HistoricAverageClimateData(**row)


class Command(BaseCommand):
    help = 'Downloads historic data from a remote instance and imports computed aggregates'

    def handle(self, *args, **options):
        historic = ClimateData.objects.filter(data_source__scenario__name='historical')

        import_averages(historic)

        import_baselines(historic)
