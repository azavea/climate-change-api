from settings import *

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    },
    'bypass': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    },
    'api_views': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    },
    'api_throttling': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    },
}
