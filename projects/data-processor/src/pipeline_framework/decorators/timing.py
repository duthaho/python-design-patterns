"""Timing decorator for performance measurement."""

import time
from typing import Dict, Optional

from pipeline_framework.core.models import ProcessingContext
from pipeline_framework.core.processor import Processor
from pipeline_framework.decorators.base import ProcessorDecorator


class TimingDecorator(ProcessorDecorator):
    """
    Decorator that measures processor execution time.
    """

    def __init__(self, wrapped: Processor, name: Optional[str] = None):
        """
        Initialize timing decorator.

        Args:
            wrapped: Processor to wrap
            name: Optional decorator name
        """
        super().__init__(wrapped, name or f"Timing({wrapped.name})")
        self._total_time = 0.0
        self._call_count = 0
        self._min_time = float("inf")
        self._max_time = 0.0

    def _do_process(self, context: ProcessingContext) -> ProcessingContext:
        """
        Process with timing.

        Steps:
        1. Record start time
        2. Call wrapped processor
        3. Record end time
        4. Calculate duration
        5. Update statistics (total_time, call_count, min_time, max_time)
        6. Add metadata to context: processing_time_ms
        """
        start_time = time.time()
        result_context = self.wrapped._do_process(context)
        end_time = time.time()

        duration = end_time - start_time
        self._total_time += duration
        self._call_count += 1
        self._min_time = min(self._min_time, duration)
        self._max_time = max(self._max_time, duration)

        result_context.data.add_metadata("processing_time_ms", duration * 1000)
        return result_context

    @property
    def timing_stats(self) -> Dict[str, float]:
        """
        Get timing statistics.

        Returns:
            Dict with total_time, call_count, avg_time, min_time, max_time
        """
        avg_time = self._total_time / self._call_count if self._call_count > 0 else 0.0
        return {
            "total_time": self._total_time,
            "call_count": self._call_count,
            "avg_time": avg_time,
            "min_time": self._min_time if self._min_time != float("inf") else 0.0,
            "max_time": self._max_time,
        }

    def reset_stats(self) -> None:
        """Reset timing statistics."""
        self._total_time = 0.0
        self._call_count = 0
        self._min_time = float("inf")
        self._max_time = 0.0
