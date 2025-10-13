"""Conditional execution strategy with event support."""

import logging
from typing import Callable, List

from ..core.context import PipelineContext
from ..core.task import Task
from ..utils.exceptions import TaskExecutionError
from .base import ExecutionStrategy

logger = logging.getLogger(__name__)


class ConditionalStrategy(ExecutionStrategy):
    """Execute tasks conditionally with event emission."""

    def __init__(self, condition: Callable[[Task, PipelineContext], bool]):
        super().__init__()
        self.condition = condition

    def execute(self, tasks: List[Task], context: PipelineContext) -> None:
        """Execute tasks conditionally with events."""
        for task in tasks:
            if self.condition(task, context):
                logger.debug(f"Executing task: {task.name}")

                # Emit task started event
                self._emit_task_event("task_started", task.name)

                try:
                    task.execute(context)
                    # Emit task completed event
                    self._emit_task_event("task_completed", task.name)
                except Exception as e:
                    # Emit task failed event
                    self._emit_task_event("task_failed", task.name, {"error": str(e)})
                    raise TaskExecutionError(task.name, e) from e
            else:
                logger.debug(f"Skipping task: {task.name} (condition not met)")
                # Optionally emit a 'task_skipped' event
                self._emit_task_event("task_skipped", task.name, {"reason": "condition not met"})
