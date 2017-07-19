import logging
from itertools import groupby

from climate_data.models import ClimateData, ClimateDataYear

from django.db import IntegrityError
from django.db.models import Max
from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Migrates data from daily ClimateData to yearly ClimateDataYear."""

    help = 'Migrates data from daily ClimateData to yearly ClimateDataYear'

    def calculate_yearly_sets(self, queryset):
        # get last day of year for this model/year
        max_days = queryset.aggregate(Max('day_of_year'))['day_of_year__max']

        # Loop over all ClimateData data points, grouped by map cell and data source
        all_data = queryset.values().order_by('map_cell', 'data_source', 'day_of_year')
        for (cell, source), data in groupby(all_data.iterator(),
                                            lambda r: (r['map_cell_id'], r['data_source_id'])):
            data = list(data)

            tasmin = [None] * max_days
            tasmax = [None] * max_days
            pr = [None] * max_days

            for datum in data:
                tasmin[datum['day_of_year']-1] = datum['tasmin']
                tasmax[datum['day_of_year']-1] = datum['tasmax']
                pr[datum['day_of_year']-1] = datum['pr']

            yield ClimateDataYear(
                map_cell_id=cell,
                data_source_id=source,
                tasmin=tasmin,
                tasmax=tasmax,
                pr=pr
            )

    def handle(self, *args, **options):
        queryset = ClimateData.objects.all()
        climate_data_years = self.calculate_yearly_sets(queryset)

        for climate_data_year in climate_data_years:
            try:
                climate_data_year.save()
            except IntegrityError:
                pass
