"""Event system for pipeline observability (Observer Pattern)."""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pipeline_framework.core.models import PipelineData, ProcessingContext

logger = logging.getLogger(__name__)


class EventType(Enum):
    """Types of pipeline events."""

    PIPELINE_STARTED = "pipeline_started"
    PIPELINE_COMPLETED = "pipeline_completed"
    PIPELINE_FAILED = "pipeline_failed"

    BATCH_STARTED = "batch_started"
    BATCH_COMPLETED = "batch_completed"

    ITEM_STARTED = "item_started"
    ITEM_COMPLETED = "item_completed"
    ITEM_FAILED = "item_failed"
    ITEM_SKIPPED = "item_skipped"

    PROCESSOR_STARTED = "processor_started"
    PROCESSOR_COMPLETED = "processor_completed"
    PROCESSOR_FAILED = "processor_failed"


@dataclass
class PipelineEvent:
    """
    Event emitted during pipeline execution.
    Contains all context about what happened.
    """

    event_type: EventType
    pipeline_id: str
    timestamp: datetime = field(default_factory=datetime.now)
    data: Optional[PipelineData] = None
    context: Optional[ProcessingContext] = None
    processor_name: Optional[str] = None
    error: Optional[Exception] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert event to dictionary for serialization.

        Returns:
            Dictionary representation of the event
        """
        return {
            "event_type": self.event_type.value,
            "pipeline_id": self.pipeline_id,
            "timestamp": self.timestamp.isoformat(),
            "data_id": self.data.id if self.data else None,
            "processor_name": self.processor_name,
            "error": str(self.error) if self.error else None,
            "metadata": self.metadata,
        }


class Observer(ABC):
    """
    Abstract observer for pipeline events.
    Implements the Observer pattern.
    """

    @abstractmethod
    def on_event(self, event: PipelineEvent) -> None:
        """
        Handle a pipeline event.

        Args:
            event: The event to handle
        """
        pass

    def on_pipeline_started(self, event: PipelineEvent) -> None:
        """Hook for pipeline start. Override for custom behavior."""
        pass

    def on_pipeline_completed(self, event: PipelineEvent) -> None:
        """Hook for pipeline completion. Override for custom behavior."""
        pass

    def on_pipeline_failed(self, event: PipelineEvent) -> None:
        """Hook for pipeline failure. Override for custom behavior."""
        pass

    def on_item_completed(self, event: PipelineEvent) -> None:
        """Hook for item completion. Override for custom behavior."""
        pass

    def on_item_failed(self, event: PipelineEvent) -> None:
        """Hook for item failure. Override for custom behavior."""
        pass


class EventBus:
    """
    Central event bus for distributing events to observers.
    Implements the Observer pattern's subject.
    """

    def __init__(self):
        """Initialize event bus with empty observer list."""
        self._observers: List[Observer] = []

    def subscribe(self, observer: Observer) -> None:
        """
        Subscribe an observer to events.

        Args:
            observer: Observer to subscribe
        """
        if observer not in self._observers:
            self._observers.append(observer)

    def unsubscribe(self, observer: Observer) -> None:
        """
        Unsubscribe an observer.

        Args:
            observer: Observer to unsubscribe
        """
        if observer in self._observers:
            self._observers.remove(observer)

    def publish(self, event: PipelineEvent) -> None:
        """
        Publish event to all subscribers.

        Args:
            event: Event to publish
        """
        for observer in self._observers:
            try:
                observer.on_event(event)

                event_map = {
                    EventType.PIPELINE_STARTED: observer.on_pipeline_started,
                    EventType.PIPELINE_COMPLETED: observer.on_pipeline_completed,
                    EventType.PIPELINE_FAILED: observer.on_pipeline_failed,
                    EventType.ITEM_COMPLETED: observer.on_item_completed,
                    EventType.ITEM_FAILED: observer.on_item_failed,
                }
                if event.event_type in event_map:
                    event_map[event.event_type](event)

            except Exception as e:
                logger.error(f"Error in observer {observer.__class__.__name__}: {e}")

    def clear(self) -> None:
        """
        Remove all observers.
        """
        self._observers.clear()

    @property
    def observer_count(self) -> int:
        """Get number of subscribed observers."""
        return len(self._observers)
