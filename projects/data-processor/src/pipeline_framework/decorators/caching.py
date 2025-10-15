"""Caching decorator for processors."""

import hashlib
import json
from typing import Any, Callable, Dict, Optional

from pipeline_framework.core.models import PipelineData, ProcessingContext
from pipeline_framework.core.processor import Processor
from pipeline_framework.decorators.base import ProcessorDecorator


class CachingDecorator(ProcessorDecorator):
    """
    Decorator that caches processor results.
    """

    def __init__(
        self,
        wrapped: Processor,
        cache_key_func: Optional[Callable[[PipelineData], str]] = None,
        max_cache_size: int = 1000,
        name: Optional[str] = None,
    ):
        """
        Initialize caching decorator.

        Args:
            wrapped: Processor to wrap
            cache_key_func: Function to generate cache key from data
            max_cache_size: Maximum number of cached results
            name: Optional decorator name
        """
        super().__init__(wrapped, name or f"Caching({wrapped.name})")
        self._cache: Dict[str, PipelineData] = {}
        self._cache_key_func = cache_key_func or self._default_cache_key
        self._max_cache_size = max_cache_size
        self._hits = 0
        self._misses = 0

    def _default_cache_key(self, data: PipelineData) -> str:
        """
        Generate default cache key from data.

        Create a hash of the payload to use as cache key.
        """
        payload_str = json.dumps(data.payload, sort_keys=True)
        return hashlib.sha256(payload_str.encode()).hexdigest()

    def _do_process(self, context: ProcessingContext) -> ProcessingContext:
        """
        Process with caching.
        """
        key = self._cache_key_func(context.data)

        if key in self._cache:
            self._hits += 1
            cached_data = self._cache[key]
            cached_data.add_metadata("cache_hit", True)
            return ProcessingContext(data=cached_data, state=context.state)

        self._misses += 1
        result_context = self.wrapped._do_process(context)
        result_data = result_context.data
        result_data.add_metadata("cache_hit", False)

        if len(self._cache) >= self._max_cache_size:
            # Remove oldest entry (FIFO)
            oldest_key = next(iter(self._cache))
            del self._cache[oldest_key]

        self._cache[key] = result_data
        return result_context

    @property
    def cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dict with hits, misses, hit_rate, cache_size
        """
        total = self._hits + self._misses
        hit_rate = (self._hits / total) if total > 0 else 0.0
        return {
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": hit_rate,
            "cache_size": len(self._cache),
            "max_cache_size": self._max_cache_size,
        }

    def clear_cache(self) -> None:
        """Clear the cache."""
        self._cache.clear()
        self._hits = 0
        self._misses = 0
