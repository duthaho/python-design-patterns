"""Metrics collection and reporting."""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from pipeline_framework.observability.events import (EventType, Observer,
                                                     PipelineEvent)


@dataclass
class PipelineMetrics:
    """
    Collected metrics for a pipeline run.
    """

    pipeline_id: str
    start_time: datetime
    end_time: Optional[datetime] = None

    total_items: int = 0
    successful_items: int = 0
    failed_items: int = 0
    skipped_items: int = 0

    processor_counts: Dict[str, int] = field(default_factory=dict)
    error_counts: Dict[str, int] = field(default_factory=dict)

    @property
    def duration(self) -> Optional[timedelta]:
        """Calculate total duration."""
        if self.end_time:
            return self.end_time - self.start_time
        return None

    @property
    def success_rate(self) -> float:
        """Calculate success rate (0.0 to 1.0)."""
        if self.total_items == 0:
            return 0.0
        return self.successful_items / self.total_items

    @property
    def error_rate(self) -> float:
        """Calculate error rate (0.0 to 1.0)."""
        if self.total_items == 0:
            return 0.0
        return self.failed_items / self.total_items

    @property
    def items_per_second(self) -> Optional[float]:
        """Calculate throughput (items/second)."""
        if self.duration:
            seconds = self.duration.total_seconds()
            if seconds > 0:
                return self.total_items / seconds
        return None

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert metrics to dictionary.
        """
        return {
            "pipeline_id": self.pipeline_id,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_seconds": self.duration.total_seconds() if self.duration else None,
            "total_items": self.total_items,
            "successful_items": self.successful_items,
            "failed_items": self.failed_items,
            "skipped_items": self.skipped_items,
            "success_rate": self.success_rate,
            "error_rate": self.error_rate,
            "items_per_second": self.items_per_second,
            "processor_counts": self.processor_counts,
            "error_counts": self.error_counts,
        }


class MetricsCollector(Observer):
    """
    Observer that collects metrics about pipeline execution.
    """

    def __init__(self):
        """Initialize metrics collector."""
        self._metrics: Dict[str, PipelineMetrics] = {}
        self._current_pipeline: Optional[str] = None

    def on_event(self, event: PipelineEvent) -> None:
        """
        Collect metrics from events.
        """
        if event.event_type == EventType.PIPELINE_STARTED:
            self._current_pipeline = event.pipeline_id
            self._metrics[self._current_pipeline] = PipelineMetrics(
                pipeline_id=event.pipeline_id,
                start_time=event.timestamp,
            )
        elif event.event_type == EventType.ITEM_COMPLETED and self._current_pipeline:
            metrics = self._metrics[self._current_pipeline]
            metrics.total_items += 1
            metrics.successful_items += 1
        elif event.event_type == EventType.ITEM_FAILED and self._current_pipeline:
            metrics = self._metrics[self._current_pipeline]
            metrics.total_items += 1
            metrics.failed_items += 1
            error_type = type(event.error).__name__ if event.error else "UnknownError"
            metrics.error_counts[error_type] = metrics.error_counts.get(error_type, 0) + 1
        elif event.event_type == EventType.ITEM_SKIPPED and self._current_pipeline:
            metrics = self._metrics[self._current_pipeline]
            metrics.total_items += 1
            metrics.skipped_items += 1
        elif event.event_type == EventType.PROCESSOR_COMPLETED and self._current_pipeline:
            metrics = self._metrics[self._current_pipeline]
            processor_name = event.processor_name or "UnknownProcessor"
            metrics.processor_counts[processor_name] = (
                metrics.processor_counts.get(processor_name, 0) + 1
            )
        elif event.event_type == EventType.PIPELINE_COMPLETED and self._current_pipeline:
            metrics = self._metrics[self._current_pipeline]
            metrics.end_time = event.timestamp
            self._current_pipeline = None
        elif event.event_type == EventType.PIPELINE_FAILED and self._current_pipeline:
            metrics = self._metrics[self._current_pipeline]
            metrics.end_time = event.timestamp
            self._current_pipeline = None

    def get_metrics(self, pipeline_id: str) -> Optional[PipelineMetrics]:
        """
        Get metrics for a specific pipeline.

        Args:
            pipeline_id: Pipeline to get metrics for

        Returns:
            PipelineMetrics or None if not found
        """
        return self._metrics.get(pipeline_id)

    def get_all_metrics(self) -> Dict[str, PipelineMetrics]:
        """Get all collected metrics."""
        return self._metrics.copy()

    def clear_metrics(self, pipeline_id: Optional[str] = None) -> None:
        """
        Clear metrics.

        Args:
            pipeline_id: If provided, clear only this pipeline's metrics.
                        If None, clear all metrics.
        """
        if pipeline_id:
            self._metrics.pop(pipeline_id, None)
        else:
            self._metrics.clear()
