"""Parallel execution strategy with event support."""

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List

from ..core.context import PipelineContext
from ..core.context_threadsafe import ThreadSafePipelineContext
from ..core.task import Task
from ..utils.exceptions import TaskExecutionError
from .base import ExecutionStrategy

logger = logging.getLogger(__name__)


class ParallelStrategy(ExecutionStrategy):
    """Execute tasks in parallel with event emission."""

    def __init__(self, max_workers: int = 4):
        super().__init__()
        self.max_workers = max_workers

    def execute(self, tasks: List[Task], context: PipelineContext) -> None:
        """Execute tasks in parallel with events."""
        if not isinstance(context, ThreadSafePipelineContext):
            context = ThreadSafePipelineContext.from_context(context)

        def execute_with_events(task: Task):
            """Execute a single task with event emission."""
            self._emit_task_event("task_started", task.name)
            try:
                task.execute(context)
                self._emit_task_event("task_completed", task.name)
            except Exception as e:
                self._emit_task_event("task_failed", task.name, {"error": str(e)})
                raise TaskExecutionError(task.name, e) from e

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {executor.submit(execute_with_events, task): task for task in tasks}

            for future in as_completed(futures):
                task = futures[future]
                try:
                    future.result()
                except Exception as e:
                    # Cancel remaining tasks
                    for f in futures:
                        f.cancel()
                    raise
