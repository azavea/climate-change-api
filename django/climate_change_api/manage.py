#!/usr/bin/env python
import os
import sys
import rollbar

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE",
                          "climate_change_api.settings")

    from django.core.management import execute_from_command_line
    from django.conf import settings

    rollbar_settings = getattr(settings, 'ROLLBAR', {})
    if rollbar_settings:
        rollbar.init(rollbar_settings['access_token'],
                     rollbar_settings['environment'])
    try:
        execute_from_command_line(sys.argv)
    except:
        if rollbar_settings:
            rollbar.report_exc_info()
        raise
