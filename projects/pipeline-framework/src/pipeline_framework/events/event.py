"""Event data structures for pipeline notifications."""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Optional


class EventType(Enum):
    """Types of events that can occur in a pipeline."""

    PIPELINE_STARTED = "pipeline_started"
    PIPELINE_COMPLETED = "pipeline_completed"
    PIPELINE_FAILED = "pipeline_failed"
    TASK_STARTED = "task_started"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"


@dataclass
class PipelineEvent:
    """
    Event data for pipeline notifications.

    Attributes:
        event_type: Type of event that occurred
        pipeline_name: Name of the pipeline
        task_name: Name of the task (None for pipeline-level events)
        timestamp: When the event occurred
        metadata: Additional event-specific data (e.g., error details, duration)
    """

    event_type: EventType
    pipeline_name: str
    task_name: Optional[str] = None
    timestamp: datetime = None  # Will be set in __post_init__
    metadata: Optional[dict[str, Any]] = None

    def __post_init__(self):
        """Set timestamp if not provided."""
        if self.timestamp is None:
            self.timestamp = datetime.now()
