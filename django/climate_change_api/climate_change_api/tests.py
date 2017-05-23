"""Custom test helpers for the climate_change_api project."""

from django.conf import settings
from django.test import TestCase, override_settings


DUMMY_CACHES = {
    cache_key: {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    } for cache_key in settings.CACHES.keys()
}


@override_settings(CACHES=DUMMY_CACHES)
class DummyCacheTestCase(TestCase):
    """Django TestCase that forces all caches to the DummyCache by default."""

    pass
