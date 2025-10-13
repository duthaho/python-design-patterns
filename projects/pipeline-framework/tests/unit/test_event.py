"""Unit tests for PipelineEvent."""

from datetime import datetime

from pipeline_framework.events.event import EventType, PipelineEvent


class TestPipelineEvent:
    """Test suite for PipelineEvent."""

    def test_event_creation_minimal(self):
        """Test creating an event with minimal parameters."""
        event = PipelineEvent(event_type=EventType.PIPELINE_STARTED, pipeline_name="test_pipeline")

        assert event.event_type == EventType.PIPELINE_STARTED
        assert event.pipeline_name == "test_pipeline"
        assert event.task_name is None
        assert isinstance(event.timestamp, datetime)
        assert event.metadata is None

    def test_event_creation_with_all_parameters(self):
        """Test creating an event with all parameters."""
        timestamp = datetime.now()
        metadata = {"key": "value", "count": 42}

        event = PipelineEvent(
            event_type=EventType.TASK_STARTED,
            pipeline_name="my_pipeline",
            task_name="my_task",
            timestamp=timestamp,
            metadata=metadata,
        )

        assert event.event_type == EventType.TASK_STARTED
        assert event.pipeline_name == "my_pipeline"
        assert event.task_name == "my_task"
        assert event.timestamp == timestamp
        assert event.metadata == metadata

    def test_event_timestamp_auto_set(self):
        """Test that timestamp is automatically set if not provided."""
        before = datetime.now()
        event = PipelineEvent(event_type=EventType.TASK_COMPLETED, pipeline_name="test")
        after = datetime.now()

        assert before <= event.timestamp <= after

    def test_event_types_enum(self):
        """Test that all event types are defined."""
        assert EventType.PIPELINE_STARTED.value == "pipeline_started"
        assert EventType.PIPELINE_COMPLETED.value == "pipeline_completed"
        assert EventType.PIPELINE_FAILED.value == "pipeline_failed"
        assert EventType.TASK_STARTED.value == "task_started"
        assert EventType.TASK_COMPLETED.value == "task_completed"
        assert EventType.TASK_FAILED.value == "task_failed"

    def test_event_with_error_metadata(self):
        """Test event with error information in metadata."""
        event = PipelineEvent(
            event_type=EventType.TASK_FAILED,
            pipeline_name="test",
            task_name="failing_task",
            metadata={"error": "ValueError: Something went wrong"},
        )

        assert event.metadata["error"] == "ValueError: Something went wrong"
