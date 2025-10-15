"""Pipeline-specific commands."""

from datetime import datetime
from typing import List

from pipeline_framework.commands.base import Command
from pipeline_framework.core.models import PipelineData, ProcessingContext
from pipeline_framework.core.pipeline import Pipeline


class ExecutePipelineCommand(Command):
    """
    Command to execute a pipeline.
    """

    def __init__(self, pipeline: Pipeline, data: List[PipelineData]):
        """
        Initialize command.

        Args:
            pipeline: Pipeline to execute
            data: Data to process
        """
        super().__init__()
        self._pipeline = pipeline
        self._data = data
        self._previous_state = None

    def execute(self) -> List[ProcessingContext]:
        """
        Execute the pipeline.
        """
        # Save current state for undo
        self._previous_state = self._pipeline.get_state()

        # Execute pipeline
        result = self._pipeline.execute(self._data)

        # Mark as executed
        self._executed = True
        self._execution_time = datetime.utcnow()
        self._result = result
        return result

    def undo(self) -> None:
        """
        Undo pipeline execution by restoring previous state.

        Note:
            This doesn't re-process data, it just restores state.
        """
        if not self.can_undo():
            raise RuntimeError("Cannot undo before execute")

        if self._previous_state is not None:
            self._pipeline.set_state(self._previous_state)

        self._executed = False
        self._execution_time = None


class ClearStateCommand(Command):
    """
    Command to clear pipeline state.
    """

    def __init__(self, pipeline: Pipeline):
        """
        Initialize command.

        Args:
            pipeline: Pipeline whose state to clear
        """
        super().__init__()
        self._pipeline = pipeline
        self._saved_state = None

    def execute(self) -> None:
        """
        Clear pipeline state.
        """
        # Save current state for undo
        self._saved_state = self._pipeline.get_state()

        # Clear state
        self._pipeline.clear_state()

        # Mark as executed
        self._executed = True
        self._execution_time = datetime.utcnow()

    def undo(self) -> None:
        """
        Restore cleared state.
        """
        if not self.can_undo():
            raise RuntimeError("Cannot undo before execute")

        if self._saved_state is not None:
            self._pipeline.set_state(self._saved_state)

        self._executed = False
        self._execution_time = None
        self._result = None
