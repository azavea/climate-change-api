from settings import *

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache'
    },
    'api_throttling': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache'
    }
}
