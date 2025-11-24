# cache.py
from time import time

_CACHE: dict[str, tuple[float, object]] = {}

def cache_get(key: str):
    item = _CACHE.get(key)
    if not item:
        return None
    expires, value = item
    if time() > expires:
        del _CACHE[key]
        return None
    return value

def cache_set(key: str, value: object, ttl: int):
    _CACHE[key] = (time() + ttl, value)
