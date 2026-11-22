
import time
import threading
from functools import wraps
from collections import OrderedDict
from copy import deepcopy


def ttl_cache(ttl_seconds=600, maxsize=100):
    """Cache function results for a limited time."""

    def decorator(function):
        cache = OrderedDict()
        lock = threading.RLock()

        @wraps(function)
        def wrapper(*args, **kwargs):
            key = (args, tuple(sorted(kwargs.items())))
            current_time = time.monotonic()

            with lock:
                # Remove expired entries
                expired = [
                    item_key
                    for item_key, (expiry, _) in cache.items()
                    if current_time >= expiry
                ]

                for item_key in expired:
                    cache.pop(item_key, None)

                # Return cached result
                if key in cache:
                    expiry, result = cache[key]
                    cache.move_to_end(key)
                    print("Using cached answer.")
                    return deepcopy(result)

            # Generate a new result outside the lock
            result = function(*args, **kwargs)

            with lock:
                cache[key] = (
                    time.monotonic() + ttl_seconds,
                    deepcopy(result)
                )
                cache.move_to_end(key)

                # Keep cache within the size limit
                while len(cache) > maxsize:
                    cache.popitem(last=False)

            return result

        return wrapper

    return decorator
