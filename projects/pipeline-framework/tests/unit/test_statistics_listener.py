"""Unit tests for StatisticsListener."""

import pytest
from pipeline_framework.events.event import EventType, PipelineEvent
from pipeline_framework.events.listeners.statistics_listener import \
    StatisticsListener


class TestStatisticsListener:
    """Test suite for StatisticsListener."""

    def test_statistics_listener_initialization(self):
        """Test that statistics listener initializes with zero counts."""
        listener = StatisticsListener()

        stats = listener.get_statistics()
        assert stats["tasks_started"] == 0
        assert stats["tasks_completed"] == 0
        assert stats["tasks_failed"] == 0
        assert stats["task_names"] == []
        assert stats["failed_task_names"] == []

    def test_statistics_listener_tracks_task_started(self):
        """Test that listener tracks task started events."""
        listener = StatisticsListener()
        event = PipelineEvent(
            event_type=EventType.TASK_STARTED, pipeline_name="test", task_name="task1"
        )

        listener.on_task_started(event)

        stats = listener.get_statistics()
        assert stats["tasks_started"] == 1
        assert "task1" in stats["task_names"]

    def test_statistics_listener_tracks_multiple_tasks_started(self):
        """Test tracking multiple task started events."""
        listener = StatisticsListener()

        for i in range(3):
            event = PipelineEvent(
                event_type=EventType.TASK_STARTED, pipeline_name="test", task_name=f"task{i}"
            )
            listener.on_task_started(event)

        stats = listener.get_statistics()
        assert stats["tasks_started"] == 3
        assert len(stats["task_names"]) == 3
        assert "task0" in stats["task_names"]
        assert "task1" in stats["task_names"]
        assert "task2" in stats["task_names"]

    def test_statistics_listener_tracks_task_completed(self):
        """Test that listener tracks task completed events."""
        listener = StatisticsListener()

        # Start and complete a task
        start_event = PipelineEvent(
            event_type=EventType.TASK_STARTED, pipeline_name="test", task_name="task1"
        )
        complete_event = PipelineEvent(
            event_type=EventType.TASK_COMPLETED, pipeline_name="test", task_name="task1"
        )

        listener.on_task_started(start_event)
        listener.on_task_completed(complete_event)

        stats = listener.get_statistics()
        assert stats["tasks_started"] == 1
        assert stats["tasks_completed"] == 1
        assert stats["tasks_failed"] == 0

    def test_statistics_listener_tracks_task_failed(self):
        """Test that listener tracks task failed events."""
        listener = StatisticsListener()

        start_event = PipelineEvent(
            event_type=EventType.TASK_STARTED, pipeline_name="test", task_name="failing_task"
        )
        fail_event = PipelineEvent(
            event_type=EventType.TASK_FAILED,
            pipeline_name="test",
            task_name="failing_task",
            metadata={"error": "Test error"},
        )

        listener.on_task_started(start_event)
        listener.on_task_failed(fail_event)

        stats = listener.get_statistics()
        assert stats["tasks_started"] == 1
        assert stats["tasks_completed"] == 0
        assert stats["tasks_failed"] == 1
        assert "failing_task" in stats["failed_task_names"]

    def test_statistics_listener_calculates_success_rate(self):
        """Test that success rate is calculated correctly."""
        listener = StatisticsListener()

        # 3 tasks: 2 succeed, 1 fails
        for i in range(3):
            listener.on_task_started(
                PipelineEvent(
                    event_type=EventType.TASK_STARTED, pipeline_name="test", task_name=f"task{i}"
                )
            )

        listener.on_task_completed(
            PipelineEvent(
                event_type=EventType.TASK_COMPLETED, pipeline_name="test", task_name="task0"
            )
        )
        listener.on_task_completed(
            PipelineEvent(
                event_type=EventType.TASK_COMPLETED, pipeline_name="test", task_name="task1"
            )
        )
        listener.on_task_failed(
            PipelineEvent(event_type=EventType.TASK_FAILED, pipeline_name="test", task_name="task2")
        )

        stats = listener.get_statistics()
        assert stats["success_rate"] == pytest.approx(2.0 / 3.0)

    def test_statistics_listener_success_rate_zero_tasks(self):
        """Test that success rate is 0 when no tasks have started."""
        listener = StatisticsListener()

        stats = listener.get_statistics()
        assert stats["success_rate"] == 0

    def test_statistics_listener_reset(self):
        """Test that reset clears all statistics."""
        listener = StatisticsListener()

        # Add some statistics
        for i in range(3):
            listener.on_task_started(
                PipelineEvent(
                    event_type=EventType.TASK_STARTED, pipeline_name="test", task_name=f"task{i}"
                )
            )
            listener.on_task_completed(
                PipelineEvent(
                    event_type=EventType.TASK_COMPLETED, pipeline_name="test", task_name=f"task{i}"
                )
            )

        # Reset
        listener.reset()

        # Should be back to initial state
        stats = listener.get_statistics()
        assert stats["tasks_started"] == 0
        assert stats["tasks_completed"] == 0
        assert stats["tasks_failed"] == 0
        assert stats["task_names"] == []
        assert stats["failed_task_names"] == []
