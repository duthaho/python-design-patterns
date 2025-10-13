"""Unit tests for ConsoleListener."""

from pipeline_framework.events.event import EventType, PipelineEvent
from pipeline_framework.events.listeners.console_listener import \
    ConsoleListener


class TestConsoleListener:
    """Test suite for ConsoleListener."""

    def test_console_listener_initialization_verbose(self):
        """Test creating a verbose console listener."""
        listener = ConsoleListener(verbose=True)
        assert listener.verbose is True

    def test_console_listener_initialization_quiet(self):
        """Test creating a quiet console listener."""
        listener = ConsoleListener(verbose=False)
        assert listener.verbose is False

    def test_console_listener_prints_pipeline_started_when_verbose(self, capsys):
        """Test that pipeline started is printed when verbose."""
        listener = ConsoleListener(verbose=True)
        event = PipelineEvent(event_type=EventType.PIPELINE_STARTED, pipeline_name="test_pipeline")

        listener.on_pipeline_started(event)

        captured = capsys.readouterr()
        assert "test_pipeline" in captured.out.lower()
        assert "started" in captured.out.lower()

    def test_console_listener_silent_pipeline_started_when_not_verbose(self, capsys):
        """Test that pipeline started is NOT printed when not verbose."""
        listener = ConsoleListener(verbose=False)
        event = PipelineEvent(event_type=EventType.PIPELINE_STARTED, pipeline_name="test_pipeline")

        listener.on_pipeline_started(event)

        captured = capsys.readouterr()
        assert captured.out == ""

    def test_console_listener_prints_pipeline_completed_when_verbose(self, capsys):
        """Test that pipeline completed is printed when verbose."""
        listener = ConsoleListener(verbose=True)
        event = PipelineEvent(
            event_type=EventType.PIPELINE_COMPLETED, pipeline_name="test_pipeline"
        )

        listener.on_pipeline_completed(event)

        captured = capsys.readouterr()
        assert "test_pipeline" in captured.out.lower()
        assert "completed" in captured.out.lower() or "success" in captured.out.lower()

    def test_console_listener_prints_pipeline_failed_always(self, capsys):
        """Test that pipeline failed is ALWAYS printed (even when not verbose)."""
        listener = ConsoleListener(verbose=False)
        event = PipelineEvent(
            event_type=EventType.PIPELINE_FAILED,
            pipeline_name="test_pipeline",
            metadata={"error": "Something went wrong"},
        )

        listener.on_pipeline_failed(event)

        captured = capsys.readouterr()
        assert "test_pipeline" in captured.out.lower()
        assert "fail" in captured.out.lower()

    def test_console_listener_prints_task_started_when_verbose(self, capsys):
        """Test that task started is printed when verbose."""
        listener = ConsoleListener(verbose=True)
        event = PipelineEvent(
            event_type=EventType.TASK_STARTED, pipeline_name="test", task_name="my_task"
        )

        listener.on_task_started(event)

        captured = capsys.readouterr()
        assert "my_task" in captured.out.lower()
        assert "started" in captured.out.lower()

    def test_console_listener_prints_task_completed_when_verbose(self, capsys):
        """Test that task completed is printed when verbose."""
        listener = ConsoleListener(verbose=True)
        event = PipelineEvent(
            event_type=EventType.TASK_COMPLETED, pipeline_name="test", task_name="my_task"
        )

        listener.on_task_completed(event)

        captured = capsys.readouterr()
        assert "my_task" in captured.out.lower()
        assert "completed" in captured.out.lower()

    def test_console_listener_prints_task_failed_always(self, capsys):
        """Test that task failed is ALWAYS printed (even when not verbose)."""
        listener = ConsoleListener(verbose=False)
        event = PipelineEvent(
            event_type=EventType.TASK_FAILED,
            pipeline_name="test",
            task_name="failing_task",
            metadata={"error": "Task error"},
        )

        listener.on_task_failed(event)

        captured = capsys.readouterr()
        assert "failing_task" in captured.out.lower()
        assert "fail" in captured.out.lower()
