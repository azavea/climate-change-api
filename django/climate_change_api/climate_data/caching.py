from rest_framework_extensions.key_constructor.constructors import DefaultKeyConstructor
from rest_framework_extensions.key_constructor.bits import (ArgsKeyBit,
                                                            KwargsKeyBit,
                                                            QueryParamsKeyBit,)


class FullUrlKeyConstructor(DefaultKeyConstructor):
    args = ArgsKeyBit()
    kwargs = KwargsKeyBit()
    query_params = QueryParamsKeyBit()


full_url_cache_key_func = FullUrlKeyConstructor()
