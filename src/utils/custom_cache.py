from time import time

from cachetools import TTLCache

from log import Logger


class CustomCache:
    """ 
    Wrapper around cachetools' TTLCache. Because there are frequent calls being
    made to the database, a TTLCache is needed to not only reduce the amount of calls made
    to the database but also help with automatically cleaning the cache to prevent indefinite
    growth.
    Read more about Time-to-live (TTL): https://en.wikipedia.org/wiki/Time_to_live 
    """

    def __init__(self, maxsize=100, ttl=300):
        self.cache = TTLCache(maxsize, ttl)
        self._maxsize = maxsize
        self._ttl = ttl
        self.timestamps = {}

    def __call__(self, func):
        def wrapped_func(*args, **kwargs):
            cache_key = (func.__name__, args, frozenset(kwargs.items()))
            if cache_key in self.cache:
                cached_time = self.timestamps.get(cache_key, 0)
                current_time = time()
                diff = current_time - cached_time
                Logger.DEBUG(
                    f"cached_time: {cached_time} | current_time: {current_time} | self.cache.ttl: {self.cache.ttl}")
                Logger.DEBUG(f"diff (current time - cached time): {diff}")
                if diff < self.cache.ttl:
                    return self.cache.get(cache_key)
            result = func(*args, **kwargs)
            self.add(cache_key, result)
            return result
        return wrapped_func

    def __getitem__(self, key):
        return self.cache[key]

    def __setitem__(self, key, value):
        self.cache[key] = value

    def __delitem__(self, key):
        del self.cache[key]

    def __iter__(self):
        return iter(self.cache)

    def __len__(self):
        return len(self.cache)

    def get(self, key):
        value = self.cache.get(key)
        Logger.DEBUG("Retrieving key-value pair from cache:")
        Logger.DEBUG(f"key: {key} | value: {value}")
        return value

    def search(self, value):
        if value in self.cache:
            return value
        return None

    def add(self, key, value):
        Logger.DEBUG(
            "Key-value pair not found in cache, adding it now.")
        Logger.DEBUG(
            f"Key-value pair - key: {key} | value: {value}")
        self.timestamps[key] = time()
        self.cache[key] = value

    @property
    def maxsize(self):
        return self._maxsize

    @property
    def ttl(self):
        return self._ttl

    def keys(self):
        return list(self.cache.keys())

    def values(self):
        return list(self.cache.values())
