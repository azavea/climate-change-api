import logging
from itertools import groupby

from climate_data.models import ClimateData, ClimateDataYear

from django.db import IntegrityError
from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Migrates data from daily ClimateData to yearly ClimateDataYear."""

    help = 'Migrates data from daily ClimateData to yearly ClimateDataYear'

    def calculate_yearly_sets(self, queryset):
        # Loop over all ClimateData data points, grouped by map cell and data source
        all_data = queryset.values().order_by('map_cell', 'data_source', 'day_of_year')
        for (cell, source), data in groupby(all_data.iterator(),
                                            lambda r: (r['map_cell_id'], r['data_source_id'])):
            data = list(data)
            yield ClimateDataYear(
                map_cell_id=cell,
                data_source_id=source,
                tasmin=[x['tasmin'] for x in data],
                tasmax=[x['tasmax'] for x in data],
                pr=[x['pr'] for x in data]
            )

    def handle(self, *args, **options):
        queryset = ClimateData.objects.all()
        climate_data_years = self.calculate_yearly_sets(queryset)

        for climate_data_year in climate_data_years:
            try:
                climate_data_year.save()
            except IntegrityError:
                pass
