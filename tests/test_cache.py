from time import sleep

import pytest

from src.utils.custom_cache import CustomCache


class TestCache():

    @pytest.mark.parametrize("key, value, expected", [
        ("key1", "value1", "value1"),
        ("key2", 5.3, 5.3),
        ("someKeyHere", {"hi": {1, 2, 5}}, {"hi": {1, 2, 5}}),
        (-1, 2, 2),
        ('k', True, True),
        (2, False, False),
        ((1, 2, 3), -2, -2)
    ])
    def test_add_and_get(self, key, value, expected):
        cache = CustomCache()
        cache.add(key, value)
        result = cache.get(key)
        assert result == expected

    def test_ttl_not_expired(self):
        cache = CustomCache(ttl=2)
        cache.add("key1", 1)
        sleep(1)
        result = cache.get("key1")
        assert result == 1

    def test_ttl_expired(self):
        cache = CustomCache(ttl=1)
        cache.add("key1", 1)
        sleep(1.5)
        result = cache.get("key1")
        assert result is None

    def test_length(self):
        cache = CustomCache(maxsize=3, ttl=1)
        assert cache.maxsize == 3
        assert cache.ttl == 1

        cache.add("key1", 1)
        cache.add("key2", 2)
        cache.add("key3", 3)
        assert len(cache) == 3

        sleep(2)
        cache.add("key4", 4)

        assert len(cache) == 1

    def test_maxsize(self):
        cache = CustomCache(maxsize=2, ttl=1)
        assert cache.maxsize == 2

        cache = CustomCache(maxsize=57, ttl=1)
        assert cache.maxsize == 57

        cache = CustomCache()
        assert cache.maxsize == 100

    def test_keys(self):
        cache = CustomCache(maxsize=2)
        cache.add("key1", "value1")
        cache.add("key2", "value2")
        assert cache.keys() == ["key1", "key2"]

        cache.add("key3", 3)
        assert cache.keys() != ["key1", "key2"]

        cache2 = CustomCache(maxsize=3)
        cache2.add("key1", "value1")
        cache2.add("key2", "value2")
        cache2.add("key3", 3)
        assert cache2.keys() == ["key1", "key2", "key3"]

    def test_values(self):
        cache = CustomCache(maxsize=3)
        cache.add("key1", "value1")
        cache.add("key2", "value2")
        assert cache.values() == ["value1", "value2"]

        cache.add("key3", "value3")
        assert cache.values() != ["value2", "value3"]

    def test_ttl(self):
        cache = CustomCache()
        assert cache.ttl == 300

        cache = CustomCache(ttl=2)
        assert cache.ttl != 3

        cache = CustomCache(ttl=40)
        assert cache.ttl == 40

    def test_cache_with_multiple_funcs(self):
        cache = CustomCache(maxsize=5, ttl=10)

        def compute_factorial(n):
            if n in cache:
                return cache[n]
            else:
                result = 1
                for i in range(1, n+1):
                    result *= i
                cache[n] = result
                return result

        def compute_fibonacci(n):
            fib = 0
            if n in cache:
                return cache[n]
            else:
                if n <= 0:
                    fib = 0
                elif n == 1:
                    fib = 1
                else:
                    fib_prev = 0
                    fib_curr = 1
                    for i in range(2, n+1):
                        fib = fib_prev + fib_curr
                        fib_prev = fib_curr
                        fib_curr = fib
                cache[n] = fib
                return fib

        assert compute_factorial(5) == 120
        sleep(1)
        assert cache[5] == 120

        assert compute_fibonacci(10) == 55
        assert compute_fibonacci(0) == 0
        sleep(1)
        assert cache[10] == 55
        assert cache[0] == 0
        assert len(cache) == 3
