"""Base listener class for observing pipeline events."""

from abc import ABC
from typing import Optional

from .event import EventType, PipelineEvent


class PipelineListener(ABC):
    """
    Abstract base class for pipeline event listeners (Observer Pattern).

    Subclasses can override specific event handler methods to react to events.
    All methods have default no-op implementations, so listeners only need
    to implement the events they care about.
    """

    def on_event(self, event: PipelineEvent) -> None:
        """
        Central event dispatcher. Routes events to specific handlers.

        This method is called by the pipeline for every event.
        It routes to specific on_* methods based on event type.

        Args:
            event: The event that occurred
        """
        event_type_to_handler = {
            EventType.PIPELINE_STARTED: self.on_pipeline_started,
            EventType.PIPELINE_COMPLETED: self.on_pipeline_completed,
            EventType.PIPELINE_FAILED: self.on_pipeline_failed,
            EventType.TASK_STARTED: self.on_task_started,
            EventType.TASK_COMPLETED: self.on_task_completed,
            EventType.TASK_FAILED: self.on_task_failed,
        }
        handler = event_type_to_handler.get(event.event_type)
        if handler:
            handler(event)
        else:
            raise ValueError(f"Unhandled event type: {event.event_type}")

    # Pipeline-level events
    def on_pipeline_started(self, event: PipelineEvent) -> None:
        """
        Called when pipeline execution starts.

        Args:
            event: Event with pipeline information
        """
        pass  # Default: do nothing

    def on_pipeline_completed(self, event: PipelineEvent) -> None:
        """
        Called when pipeline completes successfully.

        Args:
            event: Event with pipeline information
        """
        pass  # Default: do nothing

    def on_pipeline_failed(self, event: PipelineEvent) -> None:
        """
        Called when pipeline execution fails.

        Args:
            event: Event with pipeline and error information
        """
        pass  # Default: do nothing

    # Task-level events
    def on_task_started(self, event: PipelineEvent) -> None:
        """
        Called when a task starts execution.

        Args:
            event: Event with task information
        """
        pass  # Default: do nothing

    def on_task_completed(self, event: PipelineEvent) -> None:
        """
        Called when a task completes successfully.

        Args:
            event: Event with task information
        """
        pass  # Default: do nothing

    def on_task_failed(self, event: PipelineEvent) -> None:
        """
        Called when a task execution fails.

        Args:
            event: Event with task and error information
        """
        pass  # Default: do nothing


class RecordingListener(PipelineListener):
    """
    Listener that records all received events.

    Useful for testing and debugging to verify event flow.
    """

    def __init__(self):
        """Initialize with empty event list."""
        self.events = []

    def on_event(self, event: PipelineEvent) -> None:
        """
        Record the event and call base implementation.

        Args:
            event: The event that occurred
        """
        self.events.append(event)
        super().on_event(event)


class ThresholdListener(PipelineListener):
    """
    Listener that triggers an alert if failures exceed a threshold.

    Tracks number of failed tasks and triggers alert if threshold exceeded.
    """

    def __init__(self, failure_threshold: int):
        """
        Initialize threshold listener.

        Args:
            failure_threshold: Number of failures to trigger alert
        """
        self.failure_threshold = failure_threshold
        self.failure_count = 0

    def on_task_failed(self, event: PipelineEvent) -> None:
        """
        Increment failure count and check against threshold.

        Args:
            event: Event with task failure information
        """
        self.failure_count += 1
        if self.failure_count >= self.failure_threshold:
            print(
                f"⚠️ Alert: Failure threshold of {self.failure_threshold} exceeded with {self.failure_count} failures!"
            )
            # Reset count after alerting
            self.failure_count = 0


class FilteredListener(PipelineListener):
    """
    Listener that filters events based on type.

    Wraps another listener and only forwards events of specified types.
    """

    def __init__(
        self, wrapped_listener: PipelineListener, event_types: Optional[set[EventType]] = None
    ):
        """
        Initialize filtered listener.

        Args:
            wrapped_listener: The listener to wrap and filter events for
            event_types: Set of event types to forward. If None, forwards all.
        """
        self.wrapped_listener = wrapped_listener
        self.event_types = event_types if event_types is not None else set(EventType)

    def on_event(self, event: PipelineEvent) -> None:
        """
        Forward event to wrapped listener if its type is in the filter set.

        Args:
            event: The event that occurred
        """
        if event.event_type in self.event_types:
            self.wrapped_listener.on_event(event)
