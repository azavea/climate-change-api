import logging
from itertools import groupby, product

from climate_data.models import ClimateData, ClimateDataCell, ClimateDataSource, ClimateDataYear

from django.db import IntegrityError
from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)

VARIABLES = ['pr', 'tasmax', 'tasmin']


class Command(BaseCommand):
    """Migrates data from daily ClimateData to yearly ClimateDataYear."""

    help = 'Migrates data from daily ClimateData to yearly ClimateDataYear'

    def calculate_yearly_sets(self, queryset, map_cell, source):
        if ClimateDataYear.objects.filter(map_cell=map_cell, data_source=source).exists():
            print("Array data for map cell {}, source {} already exists, skipping".format(
                map_cell.id, source.id))
            return

        # Loop over all ClimateData data points, grouped by map cell and data source
        all_data = queryset.filter(map_cell=map_cell, data_source=source).values()
        for (cell, source), data in groupby(all_data.iterator(),
                                            lambda r: (r['map_cell_id'], r['data_source_id'])):

            daily_rows = {}

            daily_rows = {row['day_of_year'] - 1: row for row in data}

            max_days = max(daily_rows.keys())
            flat_list = [daily_rows.get(i, {}) for i in range(max_days + 1)]

            variables = {var: [datum.get(var, None) for datum in flat_list]
                         for var in VARIABLES}

            climate_args = dict(variables,
                                map_cell_id=cell,
                                data_source_id=source)
            try:
                ClimateDataYear.objects.create(**climate_args)
            except IntegrityError:
                pass

    def handle(self, *args, **options):
        queryset = ClimateData.objects.all()

        map_cells = ClimateDataCell.objects.all()
        sources = ClimateDataSource.objects.all()

        # Create yearly climate data for all combinations of map cells and sources
        for map_cell, source in product(map_cells, sources):
            self.calculate_yearly_sets(queryset, map_cell, source)
