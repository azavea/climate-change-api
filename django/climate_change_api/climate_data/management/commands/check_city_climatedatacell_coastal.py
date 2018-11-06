from django.core.management.base import BaseCommand

from climate_data.models import City


class Command(BaseCommand):
    """Checks all cities to verify that is_coastal hasn't changed in the move to ClimateDataCell.

    This validator will only be useful during the migration of is_coastal from
    City to ClimateDataCell. Once that migration is complete, this code can be deleted.

    """

    def handle(self, *args, **options):
        for city in City.objects.all():
            for cell in city.map_cell_set.all():
                if cell.map_cell.is_coastal != city.is_coastal:
                    self.stdout.write('{} + {}: city.is_coastal {} != map_cell.is_coastal {}'
                                      .format(city.name, cell.dataset.name,
                                              city.is_coastal, cell.map_cell.is_coastal))

        self.stdout.write('Validated is_coastal for {} cities.'.format(City.objects.count()))
