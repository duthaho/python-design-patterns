"""Tests for command pattern implementation."""

from datetime import datetime

import pytest
from pipeline_framework import PipelineBuilder
from pipeline_framework.commands.base import Command, CommandHistory
from pipeline_framework.commands.pipeline_commands import (
    ClearStateCommand, ExecutePipelineCommand)
from pipeline_framework.core.models import PipelineData
from pipeline_framework.processors.stateful import CounterProcessor


class SimpleCommand(Command):
    """Simple test command."""

    def __init__(self, value: int):
        super().__init__()
        self.value = value
        self.executed_value = None

    def execute(self):
        self._executed = True
        self._execution_time = datetime.now()
        self.executed_value = self.value * 2
        self._result = self.executed_value
        return self._result

    def undo(self):
        if not self._executed:
            raise RuntimeError("Cannot undo command that hasn't been executed")
        self.executed_value = None
        self._executed = False


class UndoableCommand(Command):
    """Command that supports undo."""

    def __init__(self):
        super().__init__()
        self.state = 0

    def execute(self):
        self._executed = True
        self._execution_time = datetime.now()
        self.state += 10
        self._result = self.state
        return self._result

    def undo(self):
        if not self._executed:
            raise RuntimeError("Cannot undo")
        self.state -= 10
        self._executed = False


class NonUndoableCommand(Command):
    """Command that cannot be undone."""

    def execute(self):
        self._executed = True
        self._execution_time = datetime.now()
        self._result = "executed"
        return self._result

    def undo(self):
        raise NotImplementedError("This command cannot be undone")

    def can_undo(self):
        return False


class TestCommandBase:
    """Test Command base class."""

    def test_command_initial_state(self):
        """Test command initial state."""
        cmd = SimpleCommand(5)

        assert not cmd.is_executed
        assert cmd.execution_time is None
        assert cmd.result is None

    def test_command_execute(self):
        """Test command execution."""
        cmd = SimpleCommand(5)

        result = cmd.execute()

        assert cmd.is_executed
        assert cmd.execution_time is not None
        assert result == 10
        assert cmd.result == 10

    def test_command_undo(self):
        """Test command undo."""
        cmd = SimpleCommand(5)

        cmd.execute()
        cmd.undo()

        assert not cmd.is_executed
        assert cmd.executed_value is None

    def test_can_undo_before_execution(self):
        """Test can_undo returns False before execution."""
        cmd = UndoableCommand()

        assert not cmd.can_undo()

    def test_can_undo_after_execution(self):
        """Test can_undo returns True after execution."""
        cmd = UndoableCommand()
        cmd.execute()

        assert cmd.can_undo()

    def test_non_undoable_command(self):
        """Test command that cannot be undone."""
        cmd = NonUndoableCommand()
        cmd.execute()

        assert not cmd.can_undo()

        with pytest.raises(NotImplementedError):
            cmd.undo()


class TestCommandHistory:
    """Test CommandHistory."""

    def test_execute_command(self):
        """Test executing command through history."""
        history = CommandHistory()
        cmd = SimpleCommand(5)

        result = history.execute(cmd)

        assert result == 10
        assert history.history_size == 1
        assert cmd.is_executed

    def test_undo_command(self):
        """Test undoing a command."""
        history = CommandHistory()
        cmd = UndoableCommand()

        history.execute(cmd)
        assert cmd.state == 10

        history.undo()
        assert cmd.state == 0
        assert not cmd.is_executed

    def test_redo_command(self):
        """Test redoing a command."""
        history = CommandHistory()
        cmd = UndoableCommand()

        history.execute(cmd)
        history.undo()
        history.redo()

        assert cmd.state == 10
        assert cmd.is_executed

    def test_multiple_undo(self):
        """Test undoing multiple commands."""
        history = CommandHistory()

        cmd1 = UndoableCommand()
        cmd2 = UndoableCommand()
        cmd3 = UndoableCommand()

        history.execute(cmd1)
        history.execute(cmd2)
        history.execute(cmd3)

        assert cmd1.state == 10
        assert cmd2.state == 10
        assert cmd3.state == 10

        history.undo()  # Undo cmd3
        assert cmd3.state == 0

        history.undo()  # Undo cmd2
        assert cmd2.state == 0

        history.undo()  # Undo cmd1
        assert cmd1.state == 0

    def test_multiple_redo(self):
        """Test redoing multiple commands."""
        history = CommandHistory()

        cmd1 = UndoableCommand()
        cmd2 = UndoableCommand()

        history.execute(cmd1)
        history.execute(cmd2)
        history.undo()
        history.undo()

        history.redo()
        assert cmd1.state == 10

        history.redo()
        assert cmd2.state == 10

    def test_undo_without_commands(self):
        """Test undo raises error when no commands."""
        history = CommandHistory()

        with pytest.raises(IndexError):
            history.undo()

    def test_redo_without_undone_commands(self):
        """Test redo raises error when nothing to redo."""
        history = CommandHistory()
        cmd = UndoableCommand()

        history.execute(cmd)

        with pytest.raises(IndexError):
            history.redo()

    def test_execute_clears_redo_stack(self):
        """Test that executing new command clears redo stack."""
        history = CommandHistory()

        cmd1 = UndoableCommand()
        cmd2 = UndoableCommand()
        cmd3 = UndoableCommand()

        history.execute(cmd1)
        history.execute(cmd2)
        history.undo()  # Can redo cmd2

        history.execute(cmd3)  # This should clear redo stack

        # Now we can't redo cmd2
        with pytest.raises(IndexError):
            history.redo()

    def test_can_undo_status(self):
        """Test can_undo status."""
        history = CommandHistory()

        assert not history.can_undo()

        cmd = UndoableCommand()
        history.execute(cmd)

        assert history.can_undo()

        history.undo()
        assert not history.can_undo()

    def test_can_redo_status(self):
        """Test can_redo status."""
        history = CommandHistory()
        cmd = UndoableCommand()

        history.execute(cmd)
        assert not history.can_redo()

        history.undo()
        assert history.can_redo()

        history.redo()
        assert not history.can_redo()

    def test_max_history_limit(self):
        """Test that history respects max size."""
        history = CommandHistory(max_history=3)

        for i in range(5):
            history.execute(SimpleCommand(i))

        # Should only keep last 3 commands
        assert history.history_size == 3

    def test_clear_history(self):
        """Test clearing command history."""
        history = CommandHistory()

        history.execute(UndoableCommand())
        history.execute(UndoableCommand())

        history.clear()

        assert history.history_size == 0
        assert not history.can_undo()
        assert not history.can_redo()


class TestExecutePipelineCommand:
    """Test ExecutePipelineCommand."""

    def test_execute_pipeline_command(self):
        """Test executing pipeline through command."""
        pipeline = PipelineBuilder("test-pipeline").add_processor(CounterProcessor()).build()

        data = [
            PipelineData.create(payload={"value": 1}),
            PipelineData.create(payload={"value": 2}),
        ]

        cmd = ExecutePipelineCommand(pipeline, data)
        results = cmd.execute()

        assert len(results) == 2
        assert cmd.is_executed
        assert pipeline.get_state()["processed_count"] == 2

    def test_undo_pipeline_command(self):
        """Test undoing pipeline execution."""
        pipeline = PipelineBuilder("test-pipeline").add_processor(CounterProcessor()).build()

        # Execute once to establish initial state
        data1 = [PipelineData.create(payload={"value": 1})]
        pipeline.execute(data1)
        initial_count = pipeline.get_state()["processed_count"]

        # Execute through command
        data2 = [PipelineData.create(payload={"value": 2})]
        cmd = ExecutePipelineCommand(pipeline, data2)
        cmd.execute()

        assert pipeline.get_state()["processed_count"] == initial_count + 1

        # Undo should restore previous state
        cmd.undo()

        assert pipeline.get_state()["processed_count"] == initial_count

    def test_execute_command_stores_result(self):
        """Test that command stores execution result."""
        pipeline = PipelineBuilder("test-pipeline").add_processor(CounterProcessor()).build()

        data = [PipelineData.create(payload={})]
        cmd = ExecutePipelineCommand(pipeline, data)

        result = cmd.execute()

        assert cmd.result == result
        assert len(cmd.result) == 1

    def test_pipeline_command_with_history(self):
        """Test pipeline command with command history."""
        history = CommandHistory()

        pipeline = PipelineBuilder("test-pipeline").add_processor(CounterProcessor()).build()

        # Execute multiple batches
        data1 = [PipelineData.create(payload={"batch": 1})]
        data2 = [PipelineData.create(payload={"batch": 2})]
        data3 = [PipelineData.create(payload={"batch": 3})]

        history.execute(ExecutePipelineCommand(pipeline, data1))
        history.execute(ExecutePipelineCommand(pipeline, data2))
        history.execute(ExecutePipelineCommand(pipeline, data3))

        assert pipeline.get_state()["processed_count"] == 3

        # Undo last batch
        history.undo()
        assert pipeline.get_state()["processed_count"] == 2

        # Undo another
        history.undo()
        assert pipeline.get_state()["processed_count"] == 1

        # Redo
        history.redo()
        assert pipeline.get_state()["processed_count"] == 2


class TestClearStateCommand:
    """Test ClearStateCommand."""

    def test_clear_state_command(self):
        """Test clearing pipeline state."""
        pipeline = PipelineBuilder("test-pipeline").add_processor(CounterProcessor()).build()

        # Build up some state
        data = [PipelineData.create(payload={}) for _ in range(5)]
        pipeline.execute(data)

        assert pipeline.get_state()["processed_count"] == 5

        # Clear state
        cmd = ClearStateCommand(pipeline)
        cmd.execute()

        assert pipeline.get_state() == {}

    def test_undo_clear_state(self):
        """Test undoing state clear."""
        pipeline = PipelineBuilder("test-pipeline").add_processor(CounterProcessor()).build()

        # Build up state
        data = [PipelineData.create(payload={}) for _ in range(3)]
        pipeline.execute(data)

        # Clear and undo
        cmd = ClearStateCommand(pipeline)
        cmd.execute()
        cmd.undo()

        # State should be restored
        assert pipeline.get_state()["processed_count"] == 3

    def test_clear_state_with_history(self):
        """Test clear state command with history."""
        history = CommandHistory()

        pipeline = PipelineBuilder("test-pipeline").add_processor(CounterProcessor()).build()

        # Build up state
        data = [PipelineData.create(payload={})]
        history.execute(ExecutePipelineCommand(pipeline, data))
        history.execute(ExecutePipelineCommand(pipeline, data))

        assert pipeline.get_state()["processed_count"] == 2

        # Clear state
        history.execute(ClearStateCommand(pipeline))
        assert pipeline.get_state() == {}

        # Undo clear
        history.undo()
        assert pipeline.get_state()["processed_count"] == 2

        # Redo clear
        history.redo()
        assert pipeline.get_state() == {}


class TestCommandPatternIntegration:
    """Integration tests for command pattern."""

    def test_complex_command_sequence(self):
        """Test complex sequence of commands."""
        history = CommandHistory()

        pipeline = PipelineBuilder("test-pipeline").add_processor(CounterProcessor()).build()

        # Execute several batches
        batch1 = [PipelineData.create(payload={"n": i}) for i in range(2)]
        batch2 = [PipelineData.create(payload={"n": i}) for i in range(3)]

        history.execute(ExecutePipelineCommand(pipeline, batch1))
        assert pipeline.get_state()["processed_count"] == 2

        history.execute(ExecutePipelineCommand(pipeline, batch2))
        assert pipeline.get_state()["processed_count"] == 5

        # Clear state
        history.execute(ClearStateCommand(pipeline))
        assert pipeline.get_state() == {}

        # Undo clear
        history.undo()
        assert pipeline.get_state()["processed_count"] == 5

        # Undo batch2
        history.undo()
        assert pipeline.get_state()["processed_count"] == 2

        # Redo batch2
        history.redo()
        assert pipeline.get_state()["processed_count"] == 5

    def test_command_history_with_failures(self):
        """Test command history handles failures gracefully."""
        history = CommandHistory()

        class FailingCommand(Command):
            def execute(self):
                self._executed = True
                raise ValueError("Command failed")

            def undo(self):
                pass

        # Execute successful command
        cmd1 = SimpleCommand(1)
        history.execute(cmd1)

        # Try to execute failing command
        cmd2 = FailingCommand()
        with pytest.raises(ValueError):
            history.execute(cmd2)

        # History should only have the successful command
        assert history.history_size == 1

        # Can still undo the successful one
        history.undo()
        assert not cmd1.is_executed

    def test_command_execution_time_tracking(self):
        """Test that commands track execution time."""
        cmd = SimpleCommand(5)

        assert cmd.execution_time is None

        cmd.execute()

        assert cmd.execution_time is not None
        assert isinstance(cmd.execution_time, datetime)

    def test_history_max_size_fifo(self):
        """Test that history uses FIFO when exceeding max size."""
        history = CommandHistory(max_history=3)

        commands = [SimpleCommand(i) for i in range(5)]

        for cmd in commands:
            history.execute(cmd)

        # Should only keep last 3
        assert history.history_size == 3

        # Should be able to undo 3 times
        history.undo()
        history.undo()
        history.undo()

        assert not history.can_undo()

    def test_command_result_persistence(self):
        """Test that command results persist."""
        history = CommandHistory()

        pipeline = PipelineBuilder("test-pipeline").add_processor(CounterProcessor()).build()

        data = [PipelineData.create(payload={}) for _ in range(3)]
        cmd = ExecutePipelineCommand(pipeline, data)

        result = history.execute(cmd)

        # Result should be accessible from command
        assert cmd.result == result
        assert len(cmd.result) == 3

        # Even after undo, result should still be there
        history.undo()
        assert cmd.result is not None


class TestCommandEdgeCases:
    """Test edge cases for command pattern."""

    def test_undo_before_execute(self):
        """Test undo before execute raises error."""
        cmd = UndoableCommand()

        with pytest.raises(RuntimeError):
            cmd.undo()

    def test_empty_history_operations(self):
        """Test operations on empty history."""
        history = CommandHistory()

        assert history.history_size == 0
        assert not history.can_undo()
        assert not history.can_redo()

        with pytest.raises(IndexError):
            history.undo()

        with pytest.raises(IndexError):
            history.redo()

    def test_clear_during_undo_redo(self):
        """Test clearing history during undo/redo operations."""
        history = CommandHistory()

        cmd1 = UndoableCommand()
        cmd2 = UndoableCommand()

        history.execute(cmd1)
        history.execute(cmd2)
        history.undo()

        # Clear while in middle of history
        history.clear()

        assert not history.can_undo()
        assert not history.can_redo()

    def test_command_reexecution(self):
        """Test executing the same command multiple times."""
        cmd = SimpleCommand(5)

        result1 = cmd.execute()
        result2 = cmd.execute()  # Execute again

        # Both should succeed and produce same result
        assert result1 == result2
        assert cmd.is_executed

    def test_pipeline_command_with_empty_data(self):
        """Test pipeline command with empty data batch."""
        pipeline = PipelineBuilder("test-pipeline").add_processor(CounterProcessor()).build()

        cmd = ExecutePipelineCommand(pipeline, [])
        result = cmd.execute()

        assert result == []
        assert cmd.is_executed
