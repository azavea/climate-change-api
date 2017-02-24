import logging

from django.core.management.base import BaseCommand

from user_management.models import ClimateUser


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Set custom throttling values on a specific API user

    Example usage:
    ./manage.py set_throttling_rates testuser@test.com --burst 10000/day
    """

    help = ('Set throttling rates for specified user from the command line.')

    def add_arguments(self, parser):
        parser.add_argument('user_email', type=str)
        parser.add_argument('--burst', type=str, default=False)
        parser.add_argument('--sustained', type=str, default=False)

    def handle(self, *args, **options):
        # Require at least one throttling rate value
        if not options['burst'] or options['sustained']:
            logger.error("Error: Set at least one throttling value")
            return

        email = options['user_email']
        user = ClimateUser.objects.get(email=email)
        if options['burst']:
            user.burst_rate = options['burst']
        if options['sustained']:
            user.sustained_rate = options['sustained']
        print "Set throttling rate(s) on " + email
