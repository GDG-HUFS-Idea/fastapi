from functools import lru_cache
import hashlib

def cache_response(func):
    @lru_cache(maxsize=128)
    def wrapper(*args, **kwargs):
        query = kwargs.get('query', args[1] if len(args) > 1 else None)
        cache_key = hashlib.md5(query.encode()).hexdigest()
        return func(*args, **kwargs)
    return wrapper
