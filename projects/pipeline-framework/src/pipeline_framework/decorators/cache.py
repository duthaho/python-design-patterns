"""Cache decorator for caching task results."""

import hashlib
import json
import logging
from typing import Any, Dict, Optional

from ..core.context import PipelineContext
from ..core.task import Task
from .base import TaskDecorator

logger = logging.getLogger(__name__)


class CacheDecorator(TaskDecorator):
    """
    Decorator that caches task results based on context state.

    If context state matches a previous execution, skip task and restore cached results.
    """

    def __init__(self, wrapped_task: Task, cache_keys: Optional[list] = None):
        """
        Initialize cache decorator.

        Args:
            wrapped_task: Task to wrap
            cache_keys: List of context keys to use for cache key.
                       If None, uses all context data.
        """
        super().__init__(wrapped_task)
        self.cache_keys = cache_keys
        self._cache: Dict[str, Dict[str, Any]] = {}

    def _compute_cache_key(self, context: PipelineContext) -> str:
        """
        Compute cache key from context.

        Args:
            context: Pipeline context

        Returns:
            Cache key string
        """
        if self.cache_keys:
            data = {k: context.get(k) for k in self.cache_keys if context.has(k)}
        else:
            data = context.get_all()
        
        json_str = json.dumps(data, sort_keys=True)
        return hashlib.md5(json_str.encode()).hexdigest()

    def execute(self, context: PipelineContext) -> None:
        """
        Execute with caching.

        Args:
            context: Pipeline context
        """
        cache_key = self._compute_cache_key(context)
        
        if cache_key in self._cache:
            logger.info(f"Cache hit for task {self.name}")
            cached_data = self._cache[cache_key]
            for key, value in cached_data.items():
                context.set(key, value)
        else:
            logger.info(f"Cache miss for task {self.name}")
            before_keys = set(context.get_all().keys())
            self._wrapped.execute(context)
            after_data = context.get_all()
            # Cache only new/modified keys
            new_data = {k: v for k, v in after_data.items() if k not in before_keys or after_data[k] != before_keys}
            self._cache[cache_key] = new_data
