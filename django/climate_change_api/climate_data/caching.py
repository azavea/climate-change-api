import logging

from rest_framework_extensions.cache.decorators import get_cache, CacheResponse
from rest_framework_extensions.cache.mixins import BaseCacheResponseMixin

from rest_framework_extensions.key_constructor.constructors import DefaultKeyConstructor
from rest_framework_extensions.key_constructor.bits import (ArgsKeyBit,
                                                            KwargsKeyBit,
                                                            QueryParamsKeyBit,)

logger = logging.getLogger(__name__)


class FullUrlKeyConstructor(DefaultKeyConstructor):
    args = ArgsKeyBit()
    kwargs = KwargsKeyBit()
    query_params = QueryParamsKeyBit()


full_url_cache_key_func = FullUrlKeyConstructor()


class OverridableCacheResponse(CacheResponse):
    """
    Modify the behavior of drf-extensions caching to allow per-query cache disabling via parameter
    (noCache=True).

    Requires the settings cache configuration to contain both a `default` and a `bypass`
    cache alias defined (use DummyCache to bypass).
    """
    def __init__(self, timeout=None,
                 key_func=None,
                 cache=None,
                 cache_errors=None,
                 bypass_cache='bypass'):
        super(OverridableCacheResponse, self).__init__(timeout, key_func, cache, cache_errors)
        self.default_cache = self.cache
        self.bypass_cache = get_cache(bypass_cache)

    def process_cache_response(self, view_instance, view_method, request, *args, **kwargs):
        nocache_param = request.query_params.get('noCache', '')
        if nocache_param and nocache_param == 'True' or nocache_param == 'true':
            self.cache = self.bypass_cache
        else:
            self.cache = self.default_cache
        return super(OverridableCacheResponse, self).process_cache_response(view_instance,
                                                                            view_method,
                                                                            request,
                                                                            *args,
                                                                            **kwargs)


overridable_cache_response = OverridableCacheResponse

# Following classes from:
# https://github.com/chibisov/drf-extensions/blob/master/rest_framework_extensions/cache/mixins.py
# Only modified to change `cache_response` decorator


class OverridableListCacheResponseMixin(BaseCacheResponseMixin):
    @overridable_cache_response(key_func='list_cache_key_func')
    def list(self, request, *args, **kwargs):
        return super(OverridableListCacheResponseMixin, self).list(request, *args, **kwargs)


class OverridableRetrieveCacheResponseMixin(BaseCacheResponseMixin):
    @overridable_cache_response(key_func='object_cache_key_func')
    def retrieve(self, request, *args, **kwargs):
        return super(OverridableRetrieveCacheResponseMixin, self).retrieve(request, *args, **kwargs)


class OverridableCacheResponseMixin(OverridableRetrieveCacheResponseMixin,
                                    OverridableListCacheResponseMixin):
    pass
