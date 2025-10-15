"""Integration tests for command pattern with full pipeline."""

from pipeline_framework import PipelineBuilder
from pipeline_framework.commands.base import CommandHistory
from pipeline_framework.commands.pipeline_commands import (
    ClearStateCommand, ExecutePipelineCommand)
from pipeline_framework.core.models import PipelineData
from pipeline_framework.observability.events import EventBus
from pipeline_framework.observability.metrics import MetricsCollector
from pipeline_framework.processors.stateful import (CounterProcessor,
                                                    DeduplicationProcessor)
from pipeline_framework.processors.transform import TransformProcessor
from pipeline_framework.strategies.transform import UpperCaseTransform


class TestCommandWithFullPipeline:
    """Test commands with full pipeline features."""

    def test_command_with_multiple_processors(self):
        """Test command execution with multiple processors."""
        history = CommandHistory()

        pipeline = (
            PipelineBuilder("multi-processor")
            .add_processor(DeduplicationProcessor())
            .add_processor(TransformProcessor(UpperCaseTransform()))
            .add_processor(CounterProcessor())
            .build()
        )

        data = [
            PipelineData(id="1", payload={"name": "alice"}, metadata={}, timestamp=None),
            PipelineData(id="2", payload={"name": "bob"}, metadata={}, timestamp=None),
            PipelineData(
                id="1", payload={"name": "alice"}, metadata={}, timestamp=None
            ),  # Duplicate
        ]

        cmd = ExecutePipelineCommand(pipeline, data)
        results = history.execute(cmd)

        # Should process 3, but deduplicate 1
        assert len(results) == 3
        assert results[2].is_skip()  # Third item skipped (duplicate)
        assert pipeline.get_state()["processed_count"] == 2  # Only 2 counted

        # Undo
        history.undo()
        assert pipeline.get_state() == {}

    def test_command_with_observability(self):
        """Test commands with event bus and metrics."""
        history = CommandHistory()
        event_bus = EventBus()
        metrics = MetricsCollector()
        event_bus.subscribe(metrics)

        pipeline = (
            PipelineBuilder("observed-pipeline")
            .add_processor(CounterProcessor())
            .with_event_bus(event_bus)
            .build()
        )

        data = [PipelineData.create(payload={"n": i}) for i in range(5)]

        cmd = ExecutePipelineCommand(pipeline, data)
        history.execute(cmd)

        # Check metrics were collected
        pipeline_metrics = metrics.get_metrics("observed-pipeline")
        assert pipeline_metrics is not None
        assert pipeline_metrics.total_items == 5
        assert pipeline_metrics.successful_items == 5

    def test_command_history_replay(self):
        """Test replaying command history."""
        history = CommandHistory()

        pipeline = PipelineBuilder("replay-test").add_processor(CounterProcessor()).build()

        # Execute commands
        batch1 = [PipelineData.create(payload={"batch": 1})]
        batch2 = [PipelineData.create(payload={"batch": 2})]
        batch3 = [PipelineData.create(payload={"batch": 3})]

        history.execute(ExecutePipelineCommand(pipeline, batch1))
        history.execute(ExecutePipelineCommand(pipeline, batch2))
        history.execute(ExecutePipelineCommand(pipeline, batch3))

        assert pipeline.get_state()["processed_count"] == 3

        # Undo all
        history.undo()
        history.undo()
        history.undo()

        assert pipeline.get_state() == {}

        # Replay by redoing
        history.redo()
        assert pipeline.get_state()["processed_count"] == 1

        history.redo()
        assert pipeline.get_state()["processed_count"] == 2

        history.redo()
        assert pipeline.get_state()["processed_count"] == 3

    def test_alternating_execute_and_clear(self):
        """Test alternating execute and clear commands."""
        history = CommandHistory()

        pipeline = PipelineBuilder("alternating-test").add_processor(CounterProcessor()).build()

        data = [PipelineData.create(payload={})]

        # Execute, clear, execute, clear pattern
        history.execute(ExecutePipelineCommand(pipeline, data))
        assert pipeline.get_state()["processed_count"] == 1

        history.execute(ClearStateCommand(pipeline))
        assert pipeline.get_state() == {}

        history.execute(ExecutePipelineCommand(pipeline, data))
        assert pipeline.get_state()["processed_count"] == 1

        history.execute(ClearStateCommand(pipeline))
        assert pipeline.get_state() == {}

        # Undo all the way back
        history.undo()  # Undo second clear
        assert pipeline.get_state()["processed_count"] == 1

        history.undo()  # Undo second execute
        assert pipeline.get_state() == {}

        history.undo()  # Undo first clear
        assert pipeline.get_state()["processed_count"] == 1

        history.undo()  # Undo first execute
        assert pipeline.get_state() == {}

    def test_command_history_branching(self):
        """Test that new commands create a new branch."""
        history = CommandHistory()

        pipeline = PipelineBuilder("branch-test").add_processor(CounterProcessor()).build()

        data = [PipelineData.create(payload={})]

        # Create initial history
        history.execute(ExecutePipelineCommand(pipeline, data))
        history.execute(ExecutePipelineCommand(pipeline, data))
        history.execute(ExecutePipelineCommand(pipeline, data))

        assert pipeline.get_state()["processed_count"] == 3

        # Undo twice
        history.undo()
        history.undo()

        assert pipeline.get_state()["processed_count"] == 1

        # Execute new command - this should clear redo stack
        history.execute(ExecutePipelineCommand(pipeline, data))

        assert pipeline.get_state()["processed_count"] == 2

        # Cannot redo the old commands anymore
        assert not history.can_redo()
