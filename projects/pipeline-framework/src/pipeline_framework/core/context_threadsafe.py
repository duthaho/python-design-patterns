"""Thread-safe pipeline context for parallel execution."""

import threading
from typing import Any, Dict, Optional

from .context import PipelineContext


class ThreadSafePipelineContext(PipelineContext):
    """
    Thread-safe version of PipelineContext.

    Uses a lock to ensure thread-safe access to shared data.
    """

    def __init__(self, initial_data: Optional[Dict[str, Any]] = None):
        """
        Initialize thread-safe context.

        Args:
            initial_data: Initial context data
        """
        super().__init__(initial_data)
        self._lock = threading.Lock()

    @classmethod
    def from_context(cls, context: PipelineContext) -> "ThreadSafePipelineContext":
        """
        Create thread-safe context from regular context.

        Args:
            context: Regular PipelineContext

        Returns:
            Thread-safe version
        """
        return cls(context.get_all())

    def set(self, key: str, value: Any) -> None:
        """Thread-safe set operation."""
        with self._lock:
            super().set(key, value)

    def get(self, key: str, default: Any = None) -> Any:
        """Thread-safe get operation."""
        with self._lock:
            return super().get(key, default)

    def has(self, key: str) -> bool:
        """Thread-safe has operation."""
        with self._lock:
            return super().has(key)

    def get_all(self) -> Dict[str, Any]:
        """Thread-safe get_all operation."""
        with self._lock:
            return super().get_all()
