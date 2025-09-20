# %% HEADER
# General utility functions

# %% IMPORTS
from collections.abc import Callable, Iterator
from functools import lru_cache, update_wrapper
from math import floor
import time
from typing import Any

import arrow
from dateutil import parser


# %% FUNCTIONS
def get_parsed_date(date: str, default: str = "2020-07-31") -> arrow.Arrow:
    """Get a date from a string.

    This function uses the dateutil parser to cover different formats more easily than
    than the standard arrow.get() function. Dates with missing date parts (such as day)
    are filled in from the default date (such as 31 for day)

    Args:
        date (str): A date string. The default is "2020-07-31".

    Returns:
        arrow.Arrow: The parsed date.
    """
    date = parser.parse(date, default=arrow.get(default))
    date = arrow.get(date)
    return date


def ttl_cache(maxsize: int = 1000, typed: bool = False, ttl: int = -1) -> Callable:
    """A decorator to cache a function with a TTL, based on the LRU cache.

    Args:
        maxsize (int, optional): The maximum size of the cache. Defaults to 1000.
        typed (bool, optional): True if the function returns a typed object. Defaults to False.
        ttl (int, optional): The time to live in seconds. Defaults to -1, which means no TTL.

    Returns:
        Callable: The decorated function.
    """
    if ttl <= 0:
        ttl = 65536

    hash_gen = _ttl_hash_gen(ttl)

    def wrapper(func: Callable) -> Callable:
        @lru_cache(maxsize, typed)
        def ttl_func(ttl_hash, *args, **kwargs):
            return func(*args, **kwargs)

        def wrapped(*args, **kwargs) -> Any:
            th = next(hash_gen)
            return ttl_func(th, *args, **kwargs)

        return update_wrapper(wrapped, func)

    return wrapper


def _ttl_hash_gen(seconds: int) -> Iterator[int]:
    """A generator to generate a hash based on the current time and a TTL.

    Args:
        seconds (int): The TTL in seconds.

    Yields:
        int: The hash.
    """
    start_time = time.time()
    while True:
        yield floor((time.time() - start_time) / seconds)
