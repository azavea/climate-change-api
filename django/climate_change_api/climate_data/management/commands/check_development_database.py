from django.core.management.base import BaseCommand
from django.db.utils import ProgrammingError

from climate_data.models import (City,
                                 CityBoundary,
                                 ClimateModel,
                                 Scenario,
                                 ClimateDataYear,
                                 Region,
                                 ClimateDataBaseline,
                                 HistoricAverageClimateData)


class Command(BaseCommand):
    """Checks to see if the development database has been fully loaded."""

    def handle(self, *args, **options):
        try:
            climate_data_map_cells = \
                ClimateDataYear.objects.all().values_list(
                    'map_cell_id', flat=True).distinct()

            # Development should contain:
            # 3 Cities with Climate data
            # Region Data
            # City Boundaries
            # Climate Models
            # Scenarios
            if (City.objects.filter(map_cell_id__in=climate_data_map_cells).count() >= 3 and  # NOQA E501
                0 not in (Region.objects.all().count(),
                          Scenario.objects.all().count(),
                          ClimateDataYear.objects.all().count(),
                          CityBoundary.objects.all().count(),
                          ClimateModel.objects.all().count(),
                          ClimateDataBaseline.objects.all().count(),
                          HistoricAverageClimateData.objects.all().count())):
                self.stdout.write("Database is loaded.")
                exit(0)
            else:
                self.stdout.write("Database is not loaded.")
                exit(1)
        except ProgrammingError:
            self.stdout.write("Database is not loaded.")
            exit(1)
