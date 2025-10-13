"""Metrics decorator for collecting task execution metrics."""

import logging
import time
from typing import Any, Dict

from ..core.context import PipelineContext
from ..core.task import Task
from .base import TaskDecorator

logger = logging.getLogger(__name__)


class MetricsDecorator(TaskDecorator):
    """
    Decorator that collects execution metrics for tasks.

    Tracks: execution time, success/failure, call count.
    """

    def __init__(self, wrapped_task: Task):
        """
        Initialize metrics decorator.

        Args:
            wrapped_task: Task to wrap
        """
        super().__init__(wrapped_task)
        self.execution_count = 0
        self.success_count = 0
        self.failure_count = 0
        self.total_time = 0.0
        self.min_time = float('inf')
        self.max_time = 0.0

    def execute(self, context: PipelineContext) -> None:
        """
        Execute with metrics collection.

        Args:
            context: Pipeline context
        """
        start_time = time.time()
        try:
            self._wrapped.execute(context)
            self.success_count += 1
        except Exception as e:
            self.failure_count += 1
            raise
        finally:
            elapsed = time.time() - start_time
            self.execution_count += 1
            self.total_time += elapsed
            self.min_time = min(self.min_time, elapsed)
            self.max_time = max(self.max_time, elapsed)

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get collected metrics.

        Returns:
            Dictionary of metrics
        """
        return {
            'execution_count': self.execution_count,
            'success_count': self.success_count,
            'failure_count': self.failure_count,
            'total_time': self.total_time,
            'avg_time': self.total_time / self.execution_count if self.execution_count > 0 else 0,
            'min_time': self.min_time if self.min_time != float('inf') else 0,
            'max_time': self.max_time
        }
