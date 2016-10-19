import logging
import numpy as np

from django.core.management.base import BaseCommand

from climate_data.models import (ClimateData, ClimateDataCell, HistoricAverageClimateData,
                                 ClimateDataBaseline, ClimateModel)
from django.db.models import Avg

logger = logging.getLogger('climate_data')

CITY_URL = 'https://{domain}/api/city/?format=json'

RAWDATA_URL = 'https://{domain}/api/climate-data/{city}/historical/'
VARIABLES = ['tasmin', 'tasmax', 'pr']
MODELS = ClimateModel.objects.all()


def generate_baselines(mapcells, queryset):
    """
    Generates baselines for cells that are represented by the queryset but do not have any baseline
    objects of their own.
    """
    for cell in mapcells.filter(baseline__isnull=True):
        logger.info("Importing baselines for cell (%f,%f)", cell.lat, cell.lon)
        data = queryset.filter(map_cell=cell)

        precips = (data.filter(data_source__model=model).values_list('pr', flat=True)
                   for model in MODELS)

        precip_99ps = [np.percentile(precip, 99) if precip else None for precip in precips]

        try:
            precip_99p = np.mean(precip_99ps)
        except TypeError:
            # numpy throws a TypeError if you try to calculate the mean of a set that has
            # non-numeric values like None. That only happens if one or more of the models
            # is missing data, which means we shouldn't try to calculate the mean.
            logger.error("Missing data for cell (%f,%f)! Skipping", cell.lat, cell.lon)
            continue

        yield ClimateDataBaseline(
            map_cell=cell,
            precip_99p=precip_99p
        )


def generate_averages(mapcells, queryset):
    for cell in mapcells.filter(historic_average=None):
        logger.info("Calculating averages for cell (%f,%f)", cell.lat, cell.lon)
        existing_averages = HistoricAverageClimateData.objects.filter(map_cell=cell)
        averages = (queryset
                    .filter(map_cell=cell)
                    .values('day_of_year')
                    .exclude(day_of_year__in=existing_averages.values('day_of_year'))
                    .annotate(**{var: Avg(var) for var in VARIABLES}))
        for row in averages:
            # Each row is a dictionary with day_of_year, pr, tasmax, and tasmin. If we add map_cell
            # then it's a complete image of what we want in HistoricAverageClimateData
            row['map_cell'] = cell
            yield HistoricAverageClimateData(**row)


class Command(BaseCommand):
    help = 'Calculates historic baselines and year-over-year averages from local raw data readings'

    def handle(self, *args, **options):
        historic_data = ClimateData.objects.filter(data_source__scenario__name='historical')
        map_cells = ClimateDataCell.objects.filter(id__in=historic_data.values('map_cell'))

        logger.info("Importing averages")
        averages = generate_averages(map_cells, historic_data)
        HistoricAverageClimateData.objects.bulk_create(averages)

        logger.info("Importing baselines")
        baselines = generate_baselines(map_cells, historic_data)
        ClimateDataBaseline.objects.bulk_create(baselines)
