"""Unit tests for Pipeline with event system."""

import pytest
from pipeline_framework.core.pipeline import Pipeline
from pipeline_framework.events.event import EventType, PipelineEvent
from pipeline_framework.events.listener import PipelineListener
from tests.conftest import AddTask, FailingTask, MultiplyTask


class RecordingListener(PipelineListener):
    """Test listener that records all events."""

    def __init__(self):
        self.events = []

    def on_event(self, event: PipelineEvent) -> None:
        """Record the event and dispatch to specific handlers."""
        self.events.append(event)
        super().on_event(event)

    def on_pipeline_started(self, event: PipelineEvent) -> None:
        pass

    def on_pipeline_completed(self, event: PipelineEvent) -> None:
        pass

    def on_pipeline_failed(self, event: PipelineEvent) -> None:
        pass

    def on_task_started(self, event: PipelineEvent) -> None:
        pass

    def on_task_completed(self, event: PipelineEvent) -> None:
        pass

    def on_task_failed(self, event: PipelineEvent) -> None:
        pass


class TestPipelineWithEvents:
    """Test suite for Pipeline event emission."""

    def test_pipeline_add_listener(self):
        """Test adding a listener to pipeline."""
        pipeline = Pipeline("test")
        listener = RecordingListener()

        result = pipeline.add_listener(listener)

        assert result is pipeline  # Fluent interface
        assert len(pipeline._listeners) == 1

    def test_pipeline_add_multiple_listeners(self):
        """Test adding multiple listeners."""
        pipeline = Pipeline("test")
        listener1 = RecordingListener()
        listener2 = RecordingListener()

        pipeline.add_listener(listener1).add_listener(listener2)

        assert len(pipeline._listeners) == 2

    def test_pipeline_remove_listener(self):
        """Test removing a listener."""
        pipeline = Pipeline("test")
        listener = RecordingListener()

        pipeline.add_listener(listener)
        pipeline.remove_listener(listener)

        assert len(pipeline._listeners) == 0

    def test_pipeline_remove_nonexistent_listener(self):
        """Test that removing non-existent listener doesn't raise error."""
        pipeline = Pipeline("test")
        listener = RecordingListener()

        # Should not raise exception
        pipeline.remove_listener(listener)

    def test_pipeline_emits_pipeline_started_event(self):
        """Test that pipeline emits started event."""
        pipeline = Pipeline("test_pipeline")
        listener = RecordingListener()
        pipeline.add_listener(listener)

        pipeline.execute()

        # Find pipeline_started event
        started_events = [e for e in listener.events if e.event_type == EventType.PIPELINE_STARTED]
        assert len(started_events) == 1
        assert started_events[0].pipeline_name == "test_pipeline"

    def test_pipeline_emits_pipeline_completed_event(self):
        """Test that pipeline emits completed event."""
        pipeline = Pipeline("test_pipeline")
        listener = RecordingListener()
        pipeline.add_listener(listener)
        pipeline.add_task(AddTask("task1", 5))

        pipeline.execute()

        # Find pipeline_completed event
        completed_events = [
            e for e in listener.events if e.event_type == EventType.PIPELINE_COMPLETED
        ]
        assert len(completed_events) == 1

    def test_pipeline_emits_task_started_event(self):
        """Test that pipeline emits task started events."""
        pipeline = Pipeline("test")
        listener = RecordingListener()
        pipeline.add_listener(listener)
        pipeline.add_task(AddTask("task1", 5))

        pipeline.execute()

        # Find task_started events
        task_started = [e for e in listener.events if e.event_type == EventType.TASK_STARTED]
        assert len(task_started) == 1
        assert task_started[0].task_name == "task1"

    def test_pipeline_emits_task_completed_event(self):
        """Test that pipeline emits task completed events."""
        pipeline = Pipeline("test")
        listener = RecordingListener()
        pipeline.add_listener(listener)
        pipeline.add_task(AddTask("task1", 5))

        pipeline.execute()

        # Find task_completed events
        task_completed = [e for e in listener.events if e.event_type == EventType.TASK_COMPLETED]
        assert len(task_completed) == 1
        assert task_completed[0].task_name == "task1"

    def test_pipeline_emits_events_for_multiple_tasks(self):
        """Test that pipeline emits events for all tasks."""
        pipeline = Pipeline("test")
        listener = RecordingListener()
        pipeline.add_listener(listener)
        pipeline.add_task(AddTask("task1", 5))
        pipeline.add_task(MultiplyTask("task2", 2))

        pipeline.execute()

        # Should have events for both tasks
        task_started = [e for e in listener.events if e.event_type == EventType.TASK_STARTED]
        task_completed = [e for e in listener.events if e.event_type == EventType.TASK_COMPLETED]
        assert len(task_started) == 2
        assert len(task_completed) == 2

    def test_pipeline_emits_task_failed_event(self):
        """Test that pipeline emits task failed event on error."""
        pipeline = Pipeline("test")
        listener = RecordingListener()
        pipeline.add_listener(listener)
        pipeline.add_task(FailingTask("failing_task"))

        with pytest.raises(Exception):
            pipeline.execute()

        # Find task_failed event
        task_failed = [e for e in listener.events if e.event_type == EventType.TASK_FAILED]
        assert len(task_failed) == 1
        assert task_failed[0].task_name == "failing_task"
        assert "error" in task_failed[0].metadata

    def test_pipeline_emits_pipeline_failed_event(self):
        """Test that pipeline emits pipeline failed event on error."""
        pipeline = Pipeline("test_pipeline")
        listener = RecordingListener()
        pipeline.add_listener(listener)
        pipeline.add_task(FailingTask("failing_task"))

        with pytest.raises(Exception):
            pipeline.execute()

        # Find pipeline_failed event
        pipeline_failed = [e for e in listener.events if e.event_type == EventType.PIPELINE_FAILED]
        assert len(pipeline_failed) == 1
        assert pipeline_failed[0].pipeline_name == "test_pipeline"

    def test_pipeline_event_order(self):
        """Test that events are emitted in correct order."""
        pipeline = Pipeline("test")
        listener = RecordingListener()
        pipeline.add_listener(listener)
        pipeline.add_task(AddTask("task1", 5))

        pipeline.execute()

        event_types = [e.event_type for e in listener.events]
        expected = [
            EventType.PIPELINE_STARTED,
            EventType.TASK_STARTED,
            EventType.TASK_COMPLETED,
            EventType.PIPELINE_COMPLETED,
        ]
        assert event_types == expected

    def test_pipeline_listener_exception_does_not_break_execution(self):
        """Test that listener exceptions don't break pipeline execution."""

        class BrokenListener(PipelineListener):
            def on_task_started(self, event):
                raise RuntimeError("Listener is broken!")

        pipeline = Pipeline("test")
        broken_listener = BrokenListener()
        good_listener = RecordingListener()

        pipeline.add_listener(broken_listener)
        pipeline.add_listener(good_listener)
        pipeline.add_task(AddTask("task1", 5))

        # Should not raise exception from listener
        result = pipeline.execute()

        # Good listener should still receive events
        assert len(good_listener.events) > 0
        assert result.get("result") == 5
