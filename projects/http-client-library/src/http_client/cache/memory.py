"""
In-memory cache implementation.

Pattern: Strategy (concrete implementation)

In-memory caching stores responses in a Python dictionary.
Fast but not shared across processes.

Use cases:
- Single-process applications
- Development and testing
- Fast access, short-lived cache
"""

import time
from threading import RLock
from typing import Dict, Optional, Tuple

from ..models import Response
from .base import Cache


class MemoryCache(Cache):
    """
    In-memory cache using Python dict.

    Features:
    - TTL (time-to-live) support
    - Thread-safe with RLock
    - LRU-like eviction (optional)
    - Fast O(1) access

    Example:
        cache = MemoryCache(default_ttl=300)  # 5 minutes
        cache.set("key", response)
        cached = cache.get("key")
    """

    def __init__(self, default_ttl: Optional[int] = None, max_size: int = 1000):
        """
        Initialize memory cache.

        Args:
            default_ttl: Default time-to-live in seconds
            max_size: Maximum number of cached items
        """
        self._cache: Dict[str, Tuple[Response, float]] = {}
        self._lock = RLock()
        self.default_ttl = default_ttl
        self.max_size = max_size

    def get(self, key: str) -> Optional[Response]:
        """
        Get cached response.

        Args:
            key: Cache key

        Returns:
            Response if found and not expired, None otherwise
        """
        with self._lock:
            if key in self._cache:
                response, expiry_time = self._cache[key]
                if expiry_time is None or expiry_time > time.time():
                    return response
                else:
                    # Expired
                    del self._cache[key]
        return None

    def set(self, key: str, value: Response, ttl: Optional[int] = None) -> None:
        """
        Store response in cache.

        Args:
            key: Cache key
            value: Response to cache
            ttl: Time-to-live in seconds (overrides default)
        """
        with self._lock:
            if len(self._cache) >= self.max_size:
                self._evict_oldest()
            expiry_time = (
                time.time() + (ttl if ttl is not None else self.default_ttl)
                if (ttl or self.default_ttl)
                else None
            )
            self._cache[key] = (value, expiry_time)

    def delete(self, key: str) -> None:
        """
        Delete cached entry.

        Args:
            key: Cache key to delete
        """
        with self._lock:
            self._cache.pop(key, None)

    def clear(self) -> None:
        """
        Clear all cached entries.
        """
        with self._lock:
            self._cache = {}

    def exists(self, key: str) -> bool:
        """
        Check if key exists and is not expired.

        Args:
            key: Cache key

        Returns:
            True if exists and not expired
        """
        with self._lock:
            if key in self._cache:
                _, expiry_time = self._cache[key]
                if expiry_time is None or expiry_time > time.time():
                    return True
                else:
                    # Expired
                    del self._cache[key]
        return False

    def _evict_expired(self) -> None:
        """
        Remove expired entries.
        """
        with self._lock:
            now = time.time()
            keys_to_delete = [
                key
                for key, (_, expiry) in self._cache.items()
                if expiry is not None and expiry <= now
            ]
            for key in keys_to_delete:
                del self._cache[key]

    def _evict_oldest(self) -> None:
        """
        Evict oldest entry (LRU-like).
        """
        with self._lock:
            if self._cache:
                oldest_key = min(
                    self._cache.items(),
                    key=lambda item: item[1][1] if item[1][1] is not None else float("inf"),
                )[0]
                del self._cache[oldest_key]

    def size(self) -> int:
        """Get number of cached items"""
        with self._lock:
            return len(self._cache)

    def __repr__(self) -> str:
        return f"MemoryCache(size={self.size()}, max_size={self.max_size})"
