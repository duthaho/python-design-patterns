"""Pipeline class implementing Chain of Responsibility pattern."""

import logging
from typing import Any, Dict, List, Optional

from ..utils.exceptions import TaskExecutionError
from .context import PipelineContext
from .task import Task

logger = logging.getLogger(__name__)


class Pipeline:
    """
    A pipeline that executes tasks sequentially (Chain of Responsibility).

    Tasks are executed in the order they were added, with each task
    operating on a shared context.
    """

    def __init__(self, name: str, description: Optional[str] = None):
        """
        Initialize a pipeline.

        Args:
            name: Name of this pipeline
            description: Optional description
        """
        self.name = name
        self.description = description or ""
        self._tasks: List[Task] = []

    def add_task(self, task: Task) -> "Pipeline":
        """
        Add a task to the pipeline.

        Args:
            task: The task to add

        Returns:
            Self for method chaining (fluent interface)
        """
        if not isinstance(task, Task):
            raise ValueError("Only Task instances can be added to the pipeline.")
        self._tasks.append(task)
        return self

    def execute(self, initial_data: Optional[Dict[str, Any]] = None) -> PipelineContext:
        """
        Execute all tasks in the pipeline sequentially.

        Args:
            initial_data: Optional initial data to populate the context

        Returns:
            The final pipeline context after all tasks have executed

        Raises:
            TaskExecutionError: If any task fails (fail-fast approach)
        """
        context = PipelineContext(initial_data)
        for task in self._tasks:
            try:
                logger.info(f"Executing task: {task.name}")
                task.execute(context)
            except Exception as e:
                raise TaskExecutionError(task.name, e) from e
        return context

    def get_tasks(self) -> List[Task]:
        """
        Get a copy of the task list.

        Returns:
            List of tasks in execution order
        """
        return self._tasks.copy()

    def __repr__(self) -> str:
        """String representation of the pipeline."""
        return f"Pipeline(name='{self.name}', tasks={len(self._tasks)})"

    def __len__(self) -> int:
        """Number of tasks in the pipeline."""
        return len(self._tasks)
