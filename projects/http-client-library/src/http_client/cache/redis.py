"""
Redis cache implementation.

Pattern: Adapter

Adapts Redis API to our Cache interface.
Provides distributed caching across multiple processes/servers.

Use cases:
- Multi-process applications
- Distributed systems
- Shared cache across services
- Production deployments
"""

import pickle
from typing import Optional

from ..models import Response
from .base import Cache

try:
    import redis

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None


class RedisCache(Cache):
    """
    Redis-based cache (Adapter pattern).

    Adapts Redis API to our Cache interface.

    Example:
        cache = RedisCache(host="localhost", port=6379)
        cache.set("key", response, ttl=300)
        cached = cache.get("key")
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        default_ttl: Optional[int] = None,
        key_prefix: str = "httpclient:",
    ):
        """
        Initialize Redis cache.

        Args:
            host: Redis host
            port: Redis port
            db: Redis database number
            default_ttl: Default TTL in seconds
            key_prefix: Prefix for all keys

        Raises:
            ImportError: If redis package not installed
        """
        if not REDIS_AVAILABLE:
            raise ImportError(
                "redis package is required for RedisCache. " "Install it with: pip install redis"
            )

        self.host = host
        self.port = port
        self.db = db
        self.default_ttl = default_ttl
        self.key_prefix = key_prefix
        self.client = redis.Redis(host=self.host, port=self.port, db=self.db)

    def get(self, key: str) -> Optional[Response]:
        """
        Get cached response from Redis.

        Args:
            key: Cache key

        Returns:
            Response if found, None otherwise
        """
        full_key = self.key_prefix + key
        data = self.client.get(full_key)
        return pickle.loads(data) if data else None

    def set(self, key: str, value: Response, ttl: Optional[int] = None) -> None:
        """
        Store response in Redis.

        Args:
            key: Cache key
            value: Response to cache
            ttl: Time-to-live in seconds
        """
        full_key = self.key_prefix + key
        data = pickle.dumps(value)
        effective_ttl = ttl if ttl is not None else self.default_ttl
        if effective_ttl:
            self.client.setex(full_key, effective_ttl, data)
        else:
            self.client.set(full_key, data)

    def delete(self, key: str) -> None:
        """
        Delete cached entry from Redis.

        Args:
            key: Cache key
        """
        full_key = self.key_prefix + key
        self.client.delete(full_key)

    def clear(self) -> None:
        """
        Clear all cached entries with our prefix.
        """
        for key in self.client.scan_iter(f"{self.key_prefix}*"):
            self.client.delete(key)

    def exists(self, key: str) -> bool:
        """
        Check if key exists in Redis.

        Args:
            key: Cache key

        Returns:
            True if exists
        """
        full_key = self.key_prefix + key
        return bool(self.client.exists(full_key))

    def ping(self) -> bool:
        """
        Check Redis connection.

        Returns:
            True if Redis is reachable
        """
        try:
            return self.client.ping()
        except:
            return False

    def __repr__(self) -> str:
        return f"RedisCache(host={self.host}, port={self.port}, db={self.db})"
