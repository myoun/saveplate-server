from functools import lru_cache
import time
from typing import Callable
import inspect

def lru_with_ttl(*, ttl_seconds: int, maxsize: int=128):
    """
    A decorator to apply LRU in-memory cache to a function with defined maximum(!) TTL in seconds.
    Be design an actual TTL may be shorter then the passed value (in rare randomized cases). But it can't be higher.
    :param ttl_seconds: TTL for a cache record in seconds
    :param maxsize: Maximum size of the LRU cache (a functools.lru_cache argument)
    :return: decorated function
    """
    def deco[**P, R](foo: Callable[P, R]) -> Callable[P, R]:
        @lru_cache(maxsize=maxsize)
        def cached_with_ttl(*args, ttl_hash, **kwargs):
            return foo(*args, **kwargs)

        def inner(*args, **kwargs):
            return cached_with_ttl(*args, ttl_hash=round(time.time() / ttl_seconds), **kwargs)

        inner.__annotations__ = foo.__annotations__
        inner.__doc__ = foo.__doc__
        inner.__signature__ = inspect.signature(foo)
        inner.__name__ = foo.__name__

        return inner
    return deco
    