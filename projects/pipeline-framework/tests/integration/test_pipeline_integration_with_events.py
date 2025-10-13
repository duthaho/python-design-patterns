"""Integration tests for pipeline with events."""

import pytest
from pipeline_framework.core.pipeline import Pipeline
from pipeline_framework.events.listeners import (ConsoleListener,
                                                 StatisticsListener)
from tests.conftest import AddTask, FailingTask, MultiplyTask


class TestPipelineIntegrationWithEvents:
    """Integration tests for pipeline with event system."""

    def test_pipeline_with_statistics_listener(self):
        """Test pipeline execution with statistics collection."""
        pipeline = Pipeline("stats_test")
        stats_listener = StatisticsListener()
        pipeline.add_listener(stats_listener)

        pipeline.add_task(AddTask("task1", 10))
        pipeline.add_task(MultiplyTask("task2", 2))
        pipeline.add_task(AddTask("task3", 5))

        result = pipeline.execute()

        # Verify execution result
        assert result.get("result") == 25  # (0 + 10) * 2 + 5 = 25

        # Verify statistics
        stats = stats_listener.get_statistics()
        assert stats["tasks_started"] == 3
        assert stats["tasks_completed"] == 3
        assert stats["tasks_failed"] == 0
        assert stats["success_rate"] == 1.0

    def test_pipeline_with_statistics_listener_on_failure(self):
        """Test statistics collection when pipeline fails."""
        pipeline = Pipeline("failing_stats_test")
        stats_listener = StatisticsListener()
        pipeline.add_listener(stats_listener)

        pipeline.add_task(AddTask("task1", 10))
        pipeline.add_task(FailingTask("failing_task"))
        pipeline.add_task(AddTask("task3", 5))  # Should not execute

        with pytest.raises(Exception):
            pipeline.execute()

        # Verify statistics
        stats = stats_listener.get_statistics()
        assert stats["tasks_started"] == 2  # Only first two started
        assert stats["tasks_completed"] == 1  # Only first completed
        assert stats["tasks_failed"] == 1
        assert "failing_task" in stats["failed_task_names"]

    def test_pipeline_with_multiple_listeners(self):
        """Test pipeline with multiple listeners."""
        pipeline = Pipeline("multi_listener_test")

        stats_listener = StatisticsListener()
        console_listener = ConsoleListener(verbose=False)

        pipeline.add_listener(stats_listener)
        pipeline.add_listener(console_listener)

        pipeline.add_task(AddTask("task1", 5))
        pipeline.add_task(MultiplyTask("task2", 3))

        result = pipeline.execute()

        # Both listeners should work
        assert result.get("result") == 15
        stats = stats_listener.get_statistics()
        assert stats["tasks_completed"] == 2

    def test_console_listener_verbose_mode(self, capsys):
        """Test console listener in verbose mode."""
        pipeline = Pipeline("verbose_test")
        console_listener = ConsoleListener(verbose=True)
        pipeline.add_listener(console_listener)

        pipeline.add_task(AddTask("task1", 5))
        pipeline.execute()

        captured = capsys.readouterr()

        # Should print all events
        assert "verbose_test" in captured.out.lower() or "started" in captured.out.lower()

    def test_statistics_listener_reset(self):
        """Test that statistics listener can be reset and reused."""
        stats_listener = StatisticsListener()

        # First pipeline
        pipeline1 = Pipeline("pipeline1")
        pipeline1.add_listener(stats_listener)
        pipeline1.add_task(AddTask("task1", 5))
        pipeline1.execute()

        stats = stats_listener.get_statistics()
        assert stats["tasks_started"] == 1

        # Reset
        stats_listener.reset()

        # Second pipeline
        pipeline2 = Pipeline("pipeline2")
        pipeline2.add_listener(stats_listener)
        pipeline2.add_task(AddTask("task2", 10))
        pipeline2.add_task(MultiplyTask("task3", 2))
        pipeline2.execute()

        stats = stats_listener.get_statistics()
        assert stats["tasks_started"] == 2  # Only second pipeline
        assert stats["tasks_completed"] == 2
