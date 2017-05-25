#!/usr/bin/env python
import os
import sys

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE",
                          "climate_change_api.settings")
    from django.core.management import execute_from_command_line

    try:
        execute_from_command_line(sys.argv)
    except:
        from django.conf import settings
        rollbar_settings = getattr(settings, 'ROLLBAR', {})
        if rollbar_settings:
            import rollbar
            rollbar.init(rollbar_settings['access_token'],
                         rollbar_settings['environment'])
            rollbar.report_exc_info()
        raise
