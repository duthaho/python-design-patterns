"""
Base class for cache implementations.

Pattern: Strategy / Adapter

Key concepts:
- Define common interface for all cache implementations
- Each implementation handles storage differently
- Adapters allow using different backends (memory, Redis, etc.)
"""

from abc import ABC, abstractmethod
from typing import Optional

from ..models import Response


class Cache(ABC):
    """
    Base class for all cache implementations.

    Cache implementations store and retrieve HTTP responses
    to avoid unnecessary network calls.

    Example implementations:
    - MemoryCache: In-process caching
    - RedisCache: Distributed caching
    - FileCache: Disk-based caching (future)
    """

    @abstractmethod
    def get(self, key: str) -> Optional[Response]:
        """
        Retrieve cached response by key.

        Args:
            key: Cache key to lookup

        Returns:
            Cached Response if found, None otherwise
        """
        pass

    @abstractmethod
    def set(self, key: str, value: Response, ttl: Optional[int] = None) -> None:
        """
        Store response in cache.

        Args:
            key: Cache key to store under
            value: Response to cache
            ttl: Time-to-live in seconds (None = no expiration)
        """
        pass

    @abstractmethod
    def delete(self, key: str) -> None:
        """
        Delete cached response.

        Args:
            key: Cache key to delete
        """
        pass

    @abstractmethod
    def clear(self) -> None:
        """
        Clear all cached responses.
        """
        pass

    @abstractmethod
    def exists(self, key: str) -> bool:
        """
        Check if key exists in cache.

        Args:
            key: Cache key to check

        Returns:
            True if key exists, False otherwise
        """
        pass

    def __repr__(self) -> str:
        """String representation for debugging"""
        return f"{self.__class__.__name__}()"


def generate_cache_key(method: str, url: str, params: dict = None) -> str:
    """
    Generate a cache key from request parameters.

    Args:
        method: HTTP method (GET, POST, etc.)
        url: Request URL
        params: Query parameters

    Returns:
        Cache key string

    Example:
        >>> generate_cache_key("GET", "http://api.com/users", {"id": "123"})
        'GET:http://api.com/users?id=123'
    """
    key = method.upper() + ":" + url
    if params:
        sorted_params = sorted(params.items())
        param_str = "&".join(f"{k}={v}" for k, v in sorted_params)
        key += "?" + param_str
    return key