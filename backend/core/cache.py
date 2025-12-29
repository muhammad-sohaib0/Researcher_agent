"""
Caching Layer Module

Provides Redis cache implementation with TTL support.
Falls back to in-memory cache if Redis is unavailable.
"""

import json
import logging
from datetime import timedelta
from typing import Any, Optional, Callable
from functools import wraps

from ..core.config import get_settings

logger = logging.getLogger(__name__)

# Default TTL values
DEFAULT_TTL = timedelta(hours=1)
PAPER_METADATA_TTL = timedelta(hours=24)
SEARCH_RESULTS_TTL = timedelta(minutes=30)


class CacheBackend:
    """Base cache backend interface."""

    def get(self, key: str) -> Optional[Any]:
        raise NotImplementedError

    def set(self, key: str, value: Any, ttl: Optional[timedelta] = None) -> bool:
        raise NotImplementedError

    def delete(self, key: str) -> bool:
        raise NotImplementedError

    def clear(self) -> bool:
        raise NotImplementedError

    def close(self) -> None:
        raise NotImplementedError


class MemoryCacheBackend(CacheBackend):
    """In-memory cache backend for development and fallback."""

    def __init__(self):
        self._cache: dict = {}
        self._expiry: dict = {}

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        import time
        if key in self._expiry and self._expiry[key] < time.time():
            self.delete(key)
            return None
        return self._cache.get(key)

    def set(self, key: str, value: Any, ttl: Optional[timedelta] = None) -> bool:
        """Set value in cache with optional TTL."""
        import time
        self._cache[key] = value
        if ttl:
            self._expiry[key] = time.time() + ttl.total_seconds()
        return True

    def delete(self, key: str) -> bool:
        """Delete value from cache."""
        self._cache.pop(key, None)
        self._expiry.pop(key, None)
        return True

    def clear(self) -> bool:
        """Clear all cached values."""
        self._cache.clear()
        self._expiry.clear()
        return True

    def close(self) -> None:
        """Close cache (no-op for memory)."""
        pass


class RedisCacheBackend(CacheBackend):
    """Redis cache backend for production use."""

    def __init__(self, redis_url: str):
        import redis
        self._client = redis.Redis.from_url(redis_url, decode_responses=True)
        self._connected = True

    def get(self, key: str) -> Optional[Any]:
        """Get value from Redis."""
        try:
            import json
            value = self._client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.warning(f"Redis get error: {e}")
            return None

    def set(self, key: str, value: Any, ttl: Optional[timedelta] = None) -> bool:
        """Set value in Redis with optional TTL."""
        try:
            import json
            serialized = json.dumps(value)
            if ttl:
                self._client.setex(key, int(ttl.total_seconds()), serialized)
            else:
                self._client.set(key, serialized)
            return True
        except Exception as e:
            logger.warning(f"Redis set error: {e}")
            return False

    def delete(self, key: str) -> bool:
        """Delete value from Redis."""
        try:
            self._client.delete(key)
            return True
        except Exception as e:
            logger.warning(f"Redis delete error: {e}")
            return False

    def clear(self) -> bool:
        """Clear all cached values."""
        try:
            self._client.flushdb()
            return True
        except Exception as e:
            logger.warning(f"Redis clear error: {e}")
            return False

    def close(self) -> None:
        """Close Redis connection."""
        try:
            self._client.close()
        except Exception as e:
            logger.warning(f"Redis close error: {e}")


class CacheManager:
    """
    Unified cache manager supporting multiple backends.

    Attempts to use Redis when available, falls back to in-memory cache.
    """

    _instance: Optional['CacheManager'] = None
    _backend: Optional[CacheBackend] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self) -> None:
        """Initialize cache backend based on configuration."""
        settings = get_settings()

        if settings.redis_enabled and settings.redis_url:
            try:
                self._backend = RedisCacheBackend(settings.redis_url)
                logger.info("Using Redis cache backend")
            except Exception as e:
                logger.warning(f"Failed to connect to Redis: {e}, falling back to in-memory cache")
                self._backend = MemoryCacheBackend()
        else:
            self._backend = MemoryCacheBackend()
            logger.info("Using in-memory cache backend")

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        return self._backend.get(key)

    def set(self, key: str, value: Any, ttl: Optional[timedelta] = None) -> bool:
        """Set value in cache."""
        return self._backend.set(key, value, ttl)

    def delete(self, key: str) -> bool:
        """Delete value from cache."""
        return self._backend.delete(key)

    def clear(self) -> bool:
        """Clear all cached values."""
        return self._backend.clear()

    def close(self) -> None:
        """Close cache connection."""
        if self._backend:
            self._backend.close()

    @property
    def backend_type(self) -> str:
        """Get the type of backend being used."""
        if isinstance(self._backend, RedisCacheBackend):
            return "redis"
        return "memory"


# Paper metadata caching helpers
class PaperCache:
    """Specialized cache for paper metadata."""

    def __init__(self, cache: CacheManager):
        self._cache = cache

    def _make_key(self, source: str, identifier: str) -> str:
        """Generate cache key for paper metadata."""
        return f"paper:{source}:{identifier}"

    def get_metadata(self, source: str, identifier: str) -> Optional[dict]:
        """Get cached paper metadata."""
        key = self._make_key(source, identifier)
        return self._cache.get(key)

    def set_metadata(self, source: str, identifier: str, metadata: dict,
                     ttl: Optional[timedelta] = PAPER_METADATA_TTL) -> bool:
        """Cache paper metadata."""
        key = self._make_key(source, identifier)
        return self._cache.set(key, metadata, ttl)

    def invalidate(self, source: str, identifier: str) -> bool:
        """Invalidate cached paper metadata."""
        key = self._make_key(source, identifier)
        return self._cache.delete(key)


# Search results caching helpers
class SearchCache:
    """Specialized cache for search results."""

    def __init__(self, cache: CacheManager):
        self._cache = cache

    def _make_key(self, query: str, filters: dict) -> str:
        """Generate cache key for search results."""
        import hashlib
        filter_str = json.dumps(filters, sort_keys=True)
        combined = f"search:{query}:{filter_str}"
        return hashlib.md5(combined.encode()).hexdigest()

    def get_results(self, query: str, filters: dict) -> Optional[list]:
        """Get cached search results."""
        key = self._make_key(query, filters)
        return self._cache.get(key)

    def set_results(self, query: str, filters: dict, results: list,
                    ttl: Optional[timedelta] = SEARCH_RESULTS_TTL) -> bool:
        """Cache search results."""
        key = self._make_key(query, filters)
        return self._cache.set(key, results, ttl)

    def invalidate_query(self, query: str) -> bool:
        """Invalidate cached results for a query."""
        # Note: This is a simplified invalidation
        # In production, you might want to use a pattern-based deletion
        return True


# Global cache instance
_cache_manager: Optional[CacheManager] = None
_paper_cache: Optional[PaperCache] = None
_search_cache: Optional[SearchCache] = None


def get_cache() -> CacheManager:
    """Get global cache manager instance."""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager()
    return _cache_manager


def get_paper_cache() -> PaperCache:
    """Get paper metadata cache."""
    global _paper_cache
    if _paper_cache is None:
        _paper_cache = PaperCache(get_cache())
    return _paper_cache


def get_search_cache() -> SearchCache:
    """Get search results cache."""
    global _search_cache
    if _search_cache is None:
        _search_cache = SearchCache(get_cache())
    return _search_cache


def cached(ttl: timedelta = DEFAULT_TTL, key_prefix: str = ""):
    """
    Decorator for caching function results.

    Usage:
        @cached(ttl=timedelta(minutes=5), key_prefix="search")
        def expensive_function(query: str):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Build cache key
            cache_key_parts = [key_prefix] if key_prefix else []
            cache_key_parts.append(func.__name__)
            cache_key_parts.extend(str(arg) for arg in args)
            cache_key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
            cache_key = ":".join(cache_key_parts)

            # Try to get from cache
            cache = get_cache()
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                return cached_value

            # Call function and cache result
            result = await func(*args, **kwargs)
            cache.set(cache_key, result, ttl)
            return result

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Build cache key
            cache_key_parts = [key_prefix] if key_prefix else []
            cache_key_parts.append(func.__name__)
            cache_key_parts.extend(str(arg) for arg in args)
            cache_key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
            cache_key = ":".join(cache_key_parts)

            # Try to get from cache
            cache = get_cache()
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                return cached_value

            # Call function and cache result
            result = func(*args, **kwargs)
            cache.set(cache_key, result, ttl)
            return result

        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator
