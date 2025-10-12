"""
Tests for cache implementations.

Pattern: Strategy/Adapter (testing)
"""

import time
from datetime import timedelta
from unittest.mock import Mock

import pytest

from http_client.cache.base import Cache, generate_cache_key
from http_client.cache.memory import MemoryCache
from http_client.models import Response


class TestCacheKeyGeneration:
    """Test cache key generation"""

    def test_generate_key_simple(self):
        """Test simple cache key generation"""
        key = generate_cache_key("GET", "http://test.com")
        assert "GET" in key
        assert "http://test.com" in key

    def test_generate_key_with_params(self):
        """Test cache key with query parameters"""
        key = generate_cache_key("GET", "http://test.com", {"id": "123", "name": "test"})
        assert "id" in key or "123" in key
        assert "name" in key or "test" in key

    def test_generate_key_consistent_param_order(self):
        """Test that param order doesn't matter"""
        key1 = generate_cache_key("GET", "http://test.com", {"a": "1", "b": "2"})
        key2 = generate_cache_key("GET", "http://test.com", {"b": "2", "a": "1"})
        assert key1 == key2

    def test_generate_key_different_methods(self):
        """Test different methods generate different keys"""
        key1 = generate_cache_key("GET", "http://test.com")
        key2 = generate_cache_key("POST", "http://test.com")
        assert key1 != key2


class TestMemoryCache:
    """Test MemoryCache implementation"""

    @pytest.fixture
    def cache(self):
        """Create memory cache for testing"""
        return MemoryCache(default_ttl=10, max_size=100)

    @pytest.fixture
    def sample_response(self):
        """Create sample response for testing"""
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.headers = {"Content-Type": "application/json"}
        mock_resp.content = b'{"key": "value"}'
        mock_resp.text = '{"key": "value"}'
        mock_resp.url = "http://test.com"
        mock_resp.elapsed = timedelta(milliseconds=100)
        return Response.from_requests_response(mock_resp)

    def test_initialization(self, cache):
        """Test cache initializes correctly"""
        assert cache.default_ttl == 10
        assert cache.max_size == 100
        assert cache.size() == 0

    def test_set_and_get(self, cache, sample_response):
        """Test basic set and get"""
        cache.set("test_key", sample_response)

        result = cache.get("test_key")
        assert result is not None
        assert result.status_code == 200

    def test_get_nonexistent_key(self, cache):
        """Test get with non-existent key returns None"""
        result = cache.get("nonexistent")
        assert result is None

    def test_ttl_expiration(self, cache, sample_response):
        """Test that entries expire after TTL"""
        cache.set("test_key", sample_response, ttl=1)  # 1 second TTL

        # Should exist immediately
        assert cache.get("test_key") is not None

        # Wait for expiration
        time.sleep(1.1)

        # Should be expired
        assert cache.get("test_key") is None

    def test_delete(self, cache, sample_response):
        """Test deleting cached entry"""
        cache.set("test_key", sample_response)
        assert cache.exists("test_key")

        cache.delete("test_key")
        assert not cache.exists("test_key")

    def test_clear(self, cache, sample_response):
        """Test clearing all cached entries"""
        cache.set("key1", sample_response)
        cache.set("key2", sample_response)
        assert cache.size() == 2

        cache.clear()
        assert cache.size() == 0

    def test_exists(self, cache, sample_response):
        """Test exists check"""
        assert not cache.exists("test_key")

        cache.set("test_key", sample_response)
        assert cache.exists("test_key")

    def test_max_size_eviction(self, cache, sample_response):
        """Test that cache evicts when max_size reached"""
        cache = MemoryCache(max_size=3)

        cache.set("key1", sample_response)
        cache.set("key2", sample_response)
        cache.set("key3", sample_response)
        assert cache.size() == 3

        # Adding 4th should trigger eviction
        cache.set("key4", sample_response)
        assert cache.size() <= 3

    def test_thread_safety(self, cache, sample_response):
        """Test thread-safe operations"""
        import threading

        def set_values():
            for i in range(10):
                cache.set(f"key{i}", sample_response)

        threads = [threading.Thread(target=set_values) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Should not crash and should have some entries
        assert cache.size() > 0

    def test_custom_ttl_overrides_default(self, cache, sample_response):
        """Test that custom TTL overrides default"""
        cache.set("key1", sample_response)  # Uses default TTL (10s)
        cache.set("key2", sample_response, ttl=1)  # Custom TTL (1s)

        time.sleep(1.1)

        # key1 should still exist (10s TTL)
        assert cache.get("key1") is not None
        # key2 should be expired (1s TTL)
        assert cache.get("key2") is None


class TestRedisCacheIntegration:
    """Integration tests for RedisCache (requires Redis running)"""

    @pytest.mark.integration
    @pytest.mark.redis
    def test_redis_cache_basic_operations(self):
        """Test basic Redis cache operations"""
        try:
            from http_client.cache.redis import RedisCache
        except ImportError:
            pytest.skip("redis package not installed")

        try:
            cache = RedisCache(host="localhost", port=6379)
            if not cache.ping():
                pytest.skip("Redis not available")
        except:
            pytest.skip("Redis not available")

        # Create sample response
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.headers = {}
        mock_resp.content = b"test"
        mock_resp.text = "test"
        mock_resp.url = "http://test.com"
        mock_resp.elapsed = timedelta(milliseconds=100)
        response = Response.from_requests_response(mock_resp)

        # Test set and get
        cache.set("test_key", response, ttl=10)
        result = cache.get("test_key")

        assert result is not None
        assert result.status_code == 200

        # Cleanup
        cache.delete("test_key")

    @pytest.mark.integration
    @pytest.mark.redis
    def test_redis_cache_clear(self):
        """Test Redis cache clear"""
        try:
            from http_client.cache.redis import RedisCache

            cache = RedisCache(host="localhost", key_prefix="test:")
            if not cache.ping():
                pytest.skip("Redis not available")
        except:
            pytest.skip("Redis not available")

        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.headers = {}
        mock_resp.content = b"test"
        mock_resp.text = "test"
        mock_resp.url = "http://test.com"
        mock_resp.elapsed = timedelta(milliseconds=100)
        response = Response.from_requests_response(mock_resp)

        cache.set("key1", response)
        cache.set("key2", response)

        cache.clear()

        assert not cache.exists("key1")
        assert not cache.exists("key2")


# Parametrized tests for both cache implementations
@pytest.mark.parametrize(
    "cache_class",
    [
        MemoryCache,
        # RedisCache would go here if Redis is available
    ],
)
class TestCacheInterface:
    """Test Cache interface compliance"""

    def test_implements_cache_interface(self, cache_class):
        """Test that implementation follows Cache interface"""
        if cache_class == MemoryCache:
            cache = cache_class()
        else:
            pytest.skip("Redis not available")

        assert isinstance(cache, Cache)
        assert hasattr(cache, "get")
        assert hasattr(cache, "set")
        assert hasattr(cache, "delete")
        assert hasattr(cache, "clear")
        assert hasattr(cache, "exists")
