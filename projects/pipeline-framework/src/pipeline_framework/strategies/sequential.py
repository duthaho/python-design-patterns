"""Sequential execution strategy with event support."""

import logging
from typing import List

from ..core.context import PipelineContext
from ..core.task import Task
from ..utils.exceptions import TaskExecutionError
from .base import ExecutionStrategy

logger = logging.getLogger(__name__)


class SequentialStrategy(ExecutionStrategy):
    """Execute tasks one after another with event emission."""

    def execute(self, tasks: List[Task], context: PipelineContext) -> None:
        """Execute tasks sequentially with events."""
        for task in tasks:
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
