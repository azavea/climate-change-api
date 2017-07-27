import logging
import numpy as np
from itertools import islice
from collections import defaultdict

from django.db import IntegrityError
from django.core.management.base import BaseCommand

from climate_data.models import (ClimateData, ClimateDataCell, HistoricAverageClimateData,
                                 HistoricDateRange, ClimateDataBaseline, ClimateModel,
                                 HistoricAverageClimateDataYear, ClimateDataYear)
from django.db.models import Avg

logger = logging.getLogger('climate_data')

VARIABLES = ['tasmin', 'tasmax', 'pr']
PERCENTILES = [1, 5, 95, 99]
MODELS = ClimateModel.objects.all()

HISTORIC_PERIOD_LENGTH = 30
BATCH_SIZE = 100


def chunk_sequence(it, size):
    chunk = list(islice(it, size))
    while len(chunk) > 0:
        yield chunk
        chunk = list(islice(it, size))


def generate_year_ranges(queryset):
    """Build index of historic 30 year ranges starting at a decade+1 mark, i.e. 1971-2000."""
    historic_years = (queryset.values_list('data_source__year', flat=True)
                              .order_by('data_source__year')
                              .distinct())

    # Capture the correct start year
    start_idx = 0
    for idx, year in enumerate(historic_years):
        if (year - 1) % 10 == 0:
            start_idx = idx
            break

    # Create HistoricDateRanges from historic data
    first_end_year = historic_years[start_idx + HISTORIC_PERIOD_LENGTH - 1]
    last_possible_end_year = historic_years[len(historic_years) - 1]
    end_years = range(first_end_year, last_possible_end_year, 10)
    for end_year in end_years:
        start_year = end_year - HISTORIC_PERIOD_LENGTH + 1
        try:
            HistoricDateRange(start_year=start_year, end_year=end_year).save()
        # ignore duplicate HistoricDateRanges
        except IntegrityError:
            continue


def generate_baselines(mapcells, time_periods, queryset):
    """Build baselines for cells represented by the queryset but have no baselines of their own."""
    for cell in mapcells.filter(baseline__isnull=True):
        logger.info("Importing baselines for cell (%f,%f)", cell.lat, cell.lon)

        for period in time_periods:
            period_model_values = [queryset.filter(map_cell=cell,
                                                   data_source__model=model,
                                                   data_source__year__gte=period.start_year,
                                                   data_source__year__lte=period.end_year)
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
                    logger.error("Missing model data for cell (%f,%f)! Skipping",
                                 cell.lat, cell.lon)
                    continue

                insert_vals.update({
                    'map_cell': cell,
                    'percentile': percentile,
                    'historic_range': period,
                })

                yield ClimateDataBaseline(**insert_vals)


def generate_averages(mapcells, time_periods, queryset):
    for cell in mapcells.filter(historic_average=None):
        logger.info("Calculating averages for cell (%f,%f)", cell.lat, cell.lon)

        for period in time_periods:
            existing_averages = HistoricAverageClimateData.objects.filter(map_cell=cell,
                                                                          historic_range=period)
            averages = (queryset
                        .filter(map_cell=cell,
                                data_source__year__gte=period.start_year,
                                data_source__year__lte=period.end_year)
                        .values('day_of_year')
                        .exclude(day_of_year__in=existing_averages.values('day_of_year'))
                        .annotate(**{var: Avg(var) for var in VARIABLES}))
            for row in averages:
                # Each row is a dictionary with day_of_year, pr, tasmax, and tasmin. If we add
                # map_cell and historic_range then it's a complete image of what we want in
                # HistoricAverageClimateData
                row['map_cell'] = cell
                row['historic_range'] = period
                yield HistoricAverageClimateData(**row)


def generate_year_averages(mapcells, time_periods, queryset):
    for cell in mapcells.filter(historic_average_array=None):
        logger.info("Calculating yearly averages for cell (%f,%f)", cell.lat, cell.lon)

        for period in time_periods:
            # We can't calculate an average directly in the database, and we don't want
            # to hold all of the time period's raw data in memory either.
            # The alternative is to build the average incrementally, keeping a count
            # and sum for each day (Since some days may not have data)
            yearly_data = queryset.filter(
                map_cell=cell,
                data_source__year__gte=period.start_year,
                data_source__year__lte=period.end_year
            ).values(*VARIABLES)
            totals = {var: defaultdict(int) for var in VARIABLES}
            counts = {var: defaultdict(int) for var in VARIABLES}

            for year in yearly_data:
                for var in VARIABLES:
                    for index, val in enumerate(year[var]):
                        if val is not None:
                            totals[var][index] += float(val)
                            counts[var][index] += 1

            # Reduce the totals and counts into an ordered list of averages
            averages = {var: [totals[var][index] / counts[var][index]
                              for index in range(max(int(v) for v in totals[var].keys()))]
                        for var in VARIABLES}

            yield HistoricAverageClimateDataYear(
                **dict(averages,
                       map_cell=cell,
                       historic_range=period)
            )


class Command(BaseCommand):
    help = 'Calculates historic baselines and year-over-year averages from local raw data readings'

    def handle(self, *args, **options):
        historic_data = ClimateData.objects.filter(data_source__scenario__name='historical')
        historic_year_data = ClimateDataYear.objects.filter(
            data_source__scenario__name='historical')
        map_cells = ClimateDataCell.objects.filter(id__in=historic_data.values('map_cell'))

        logger.info("Create historic year ranges")
        generate_year_ranges(historic_data)

        time_periods = HistoricDateRange.objects.all()

        logger.info("Importing averages")
        averages = generate_averages(map_cells, time_periods, historic_data)
        for chunk in chunk_sequence(averages, BATCH_SIZE):
            HistoricAverageClimateData.objects.bulk_create(chunk)

        logger.info("Importing yearly averages")
        averages = generate_year_averages(map_cells, time_periods, historic_year_data)
        for chunk in chunk_sequence(averages, BATCH_SIZE):
            HistoricAverageClimateDataYear.objects.bulk_create(chunk)

        logger.info("Importing percentile baselines")
        baselines = generate_baselines(map_cells, time_periods, historic_data)
        for chunks in chunk_sequence(baselines, BATCH_SIZE):
            ClimateDataBaseline.objects.bulk_create(baselines)
