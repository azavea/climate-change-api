import logging
import numpy as np

from django.db import IntegrityError
from django.core.management.base import BaseCommand

from climate_data.models import (ClimateData, ClimateDataCell, HistoricAverageClimateData,
                                 HistoricDateRange, ClimateDataBaseline, ClimateModel)
from django.db.models import Avg

logger = logging.getLogger('climate_data')

CITY_URL = 'https://{domain}/api/city/?format=json'

RAWDATA_URL = 'https://{domain}/api/climate-data/{city}/historical/'
VARIABLES = ['tasmin', 'tasmax', 'pr']
PERCENTILES = [1, 5, 95, 99]
MODELS = ClimateModel.objects.all()


def generate_year_ranges(queryset):
    """Build index of historic 30 year ranges."""
    historic_years_query = queryset.values('data_source__year').distinct()
    historic_years = sorted([i['data_source__year'] for i in historic_years_query])
    years_avail = True
    start_idx = 1
    while years_avail:
        try:
            start_year = historic_years[start_idx]
            end_year = historic_years[start_idx + 30]
            HistoricDateRange(start_year=start_year, end_year=end_year).save()
            start_idx += 10
        # Ignore duplicates and continue
        except IntegrityError:
            start_idx += 10
        except IndexError:
            years_avail = False


def generate_baselines(mapcells, queryset):
    """Build baselines for cells represented by the queryset but have no baselines of their own."""
    for cell in mapcells.filter(baseline__isnull=True):
        logger.info("Importing baselines for cell (%f,%f)", cell.lat, cell.lon)
        data = queryset.filter(map_cell=cell)
        time_periods = HistoricDateRange.objects.all()

        for period in time_periods:
            period_model_values = [data.filter(data_source__model=model,
                                               data_source__year__gte=period.start_year,
                                               data_source__year__lt=period.end_year)
                                   .values(*VARIABLES)
                                   for model in MODELS]
            variable_values = {var: [[mv[var] for mv in values] for values in period_model_values]
                               for var in VARIABLES}

            # For precipitation we only want records for days that had rainfall
            variable_values['pr'] = [[x for x in vals if x > 0] for vals in variable_values['pr']]

            for percentile in PERCENTILES:
                try:
                    # Collect the percentiles by model and average them together per variable
                    insert_vals = {var: np.mean([np.percentile(vals, percentile)
                                                for vals in variable_values[var]])
                                   for var in VARIABLES}
                except TypeError:
                    # numpy throws a TypeError if you try to calculate the mean of a set that has
                    # non-numeric values like None. That only happens if one or more of the models
                    # is missing data, which means we shouldn't try to calculate the mean.
                    logger.error("Missing model data for cell (%f,%f)! Skipping", cell.lat, cell.lon)
                    continue

                insert_vals.update({
                    'map_cell': cell,
                    'percentile': percentile,
                    'date_range': period,
                })

                yield ClimateDataBaseline(**insert_vals)


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

        logger.info("Create historic year ranges")
        generate_year_ranges(historic_data)

        logger.info("Importing averages")
        averages = generate_averages(map_cells, historic_data)
        HistoricAverageClimateData.objects.bulk_create(averages)

        logger.info("Importing percentile baselines")
        baselines = generate_baselines(map_cells, historic_data)
        ClimateDataBaseline.objects.bulk_create(baselines)
