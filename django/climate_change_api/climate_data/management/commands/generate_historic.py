import logging
import numpy as np
from itertools import islice

from django.db import IntegrityError
from django.core.management.base import BaseCommand

from climate_data.models import (ClimateDataBaseline,
                                 ClimateDataCell,
                                 HistoricAverageClimateDataYear,
                                 HistoricDateRange,
                                 ClimateDataset,
                                 ClimateDataYear)

logger = logging.getLogger('climate_data')

VARIABLES = ['tasmin', 'tasmax', 'pr']
PERCENTILES = [1, 5, 95, 99]

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


def generate_baselines(dataset, mapcells, time_periods, queryset):
    """Build baselines for cells that are represented by the queryset but are missing baselines."""
    for cell in mapcells:
        if cell.baseline.count() == (time_periods.count() * len(PERCENTILES)):
            # Skip cells if they already have the right number of baselines
            continue

        logger.info("Importing baselines for cell (%f,%f)", cell.lat, cell.lon)

        # Since we're going to recalculate all baselines for a cell, delete any that currently exist
        cell.baseline.all().delete()

        for period in time_periods:
            period_model_values = [queryset.filter(map_cell=cell,
                                                   data_source__model=model,
                                                   data_source__year__gte=period.start_year,
                                                   data_source__year__lte=period.end_year)
                                   .values(*VARIABLES)
                                   for model in dataset.models.all()]
            variable_values = {var: [[v for mv in models for v in mv[var] if v is not None]
                                     for models in period_model_values]
                               for var in VARIABLES}

            # For precipitation we only want records for days that had rainfall
            variable_values['pr'] = [[x for x in vals if x > 0] for vals in variable_values['pr']]

            for percentile in PERCENTILES:
                try:
                    # Collect the percentiles by model and average them together per variable
                    insert_vals = {var: np.mean([np.percentile(vals, percentile)
                                   for vals in filter(lambda x: x != [], variable_values[var])])
                                   for var in VARIABLES}
                except TypeError:
                    # numpy throws a TypeError if you try to calculate the mean of a set that has
                    # non-numeric values like None. That only happens if one or more of the models
                    # is missing data, which means we shouldn't try to calculate the mean.
                    logger.error("Missing model data for cell (%f,%f)! Skipping",
                                 cell.lat, cell.lon)
                    continue

                yield ClimateDataBaseline(
                    map_cell=cell,
                    percentile=percentile,
                    historic_range=period,
                    dataset=dataset,
                    **insert_vals)


def generate_year_averages(dataset, mapcells, time_periods, queryset):
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

            totals = {var: [0] * 366 for var in VARIABLES}
            counts = {var: [0] * 366 for var in VARIABLES}

            # With 30 years within a historic range and 21 models, we want to average daily
            # values for 600 years worth of data. To help minimize memory pressure we can
            # keep just a running total and count, and calculate the mean from that.
            for year in yearly_data:
                for var in VARIABLES:
                    for index, val in enumerate(year[var]):
                        if val is not None:
                            totals[var][index] += float(val)
                            counts[var][index] += 1

            # Reduce the totals and counts into an ordered list of averages
            averages = {var: [total / count for total, count in zip(totals[var], counts[var])]
                        for var in VARIABLES}

            yield HistoricAverageClimateDataYear(
                map_cell=cell,
                historic_range=period,
                dataset=dataset,
                **averages)


class Command(BaseCommand):
    help = 'Calculates historic baselines and year-over-year averages from local raw data readings'

    def handle(self, *args, **options):
        # Create universal historic year range
        historic_year_data = ClimateDataYear.objects.filter(
            data_source__scenario__name='historical')
        logger.info("Create historic year range")
        generate_year_ranges(historic_year_data)

        # Create baselines for all datasets
        datasets = ClimateDataset.objects.all()

        for dataset in datasets:
            historic_year_data = ClimateDataYear.objects.filter(
                data_source__scenario__name='historical',
                data_source__dataset=dataset)

            time_periods = HistoricDateRange.objects.all()
            map_cells = ClimateDataCell.objects.filter(id__in=historic_year_data.values('map_cell'))

            logger.info("Importing yearly averages for " + dataset.name)
            averages = generate_year_averages(dataset, map_cells, time_periods, historic_year_data)
            for chunk in chunk_sequence(averages, BATCH_SIZE):
                HistoricAverageClimateDataYear.objects.bulk_create(chunk)

            logger.info("Importing percentile baselines for " + dataset.name)
            baselines = generate_baselines(dataset, map_cells, time_periods, historic_year_data)
            for chunk in chunk_sequence(baselines, BATCH_SIZE):
                ClimateDataBaseline.objects.bulk_create(chunk)
