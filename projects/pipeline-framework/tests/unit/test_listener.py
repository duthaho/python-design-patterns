"""Unit tests for PipelineListener base class."""

from pipeline_framework.events.event import EventType, PipelineEvent
from pipeline_framework.events.listener import PipelineListener


class TestListener(PipelineListener):
    """Concrete test listener for testing the base class."""

    def __init__(self):
        self.events_received = []

    def on_pipeline_started(self, event: PipelineEvent) -> None:
        self.events_received.append(("pipeline_started", event))

    def on_task_started(self, event: PipelineEvent) -> None:
        self.events_received.append(("task_started", event))


class TestPipelineListener:
    """Test suite for PipelineListener."""

    def test_listener_dispatches_pipeline_started(self):
        """Test that on_event dispatches to on_pipeline_started."""
        listener = TestListener()
        event = PipelineEvent(event_type=EventType.PIPELINE_STARTED, pipeline_name="test")

        listener.on_event(event)

        assert len(listener.events_received) == 1
        assert listener.events_received[0][0] == "pipeline_started"
        assert listener.events_received[0][1] == event

    def test_listener_dispatches_task_started(self):
        """Test that on_event dispatches to on_task_started."""
        listener = TestListener()
        event = PipelineEvent(
            event_type=EventType.TASK_STARTED, pipeline_name="test", task_name="task1"
        )

        listener.on_event(event)

        assert len(listener.events_received) == 1
        assert listener.events_received[0][0] == "task_started"

    def test_listener_default_implementations_do_nothing(self):
        """Test that default implementations don't raise errors."""
        listener = PipelineListener()

        # Should not raise any exceptions
        event = PipelineEvent(event_type=EventType.PIPELINE_COMPLETED, pipeline_name="test")

        # These should do nothing (no-op)
        listener.on_pipeline_completed(event)
        listener.on_pipeline_failed(event)
        listener.on_task_completed(event)
        listener.on_task_failed(event)

    def test_listener_handles_all_event_types(self):
        """Test that listener can handle all event types."""
        listener = TestListener()

        event_types = [
            EventType.PIPELINE_STARTED,
            EventType.PIPELINE_COMPLETED,
            EventType.PIPELINE_FAILED,
            EventType.TASK_STARTED,
            EventType.TASK_COMPLETED,
            EventType.TASK_FAILED,
        ]

        # Should not raise for any event type
        for event_type in event_types:
            event = PipelineEvent(
                event_type=event_type,
                pipeline_name="test",
                task_name="task" if "TASK" in event_type.name else None,
            )
            listener.on_event(event)
