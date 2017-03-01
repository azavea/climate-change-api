import logging

from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand

from user_management.models import ClimateUser


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Set custom throttling values on a specific API user

    Example usage:
    ./manage.py set_throttling_rates test@test.com,a@abc.com --burst 10000/day
    """

    help = ('Set throttling rates for users from the command line. '
            'Users accepted as comma-separated emails.')

    def add_arguments(self, parser):
        parser.add_argument('user_email', type=str)
        parser.add_argument('--burst', type=str, default=False)
        parser.add_argument('--sustained', type=str, default=False)

    def handle(self, *args, **options):
        # Require at least one throttling rate value
        if not (options['burst'] or options['sustained']):
            logger.error("Error: Set at least one throttling value")
            return

        emails = options['user_email'].split(',')
        burst = options['burst']
        sustained = options['sustained']

        for email in emails:
            try:
                user = ClimateUser.objects.get(email=email)
            except ObjectDoesNotExist:
                logger.warn(email + " is not a valid user")
                continue

            if burst:
                user.burst_rate = burst
            if sustained:
                user.sustained_rate = sustained
            user.save()

            logger.info("Set throttling rate(s) on " + email)
