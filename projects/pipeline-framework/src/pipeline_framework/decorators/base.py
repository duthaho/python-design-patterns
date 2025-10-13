"""Base task decorator."""

from abc import ABC
from typing import Optional

from ..core.context import PipelineContext
from ..core.task import Task


class TaskDecorator(Task, ABC):
    """
    Base class for task decorators (Decorator Pattern).

    Decorators wrap tasks to add behavior without modifying the original task.
    """

    def __init__(self, wrapped_task: Task, name: Optional[str] = None):
        """
        Initialize task decorator.

        Args:
            wrapped_task: The task to wrap
            name: Optional name override (defaults to wrapped task's name)
        """
        self._wrapped = wrapped_task
        task_name = name or wrapped_task.name
        super().__init__(task_name, wrapped_task.description)

    def execute(self, context: PipelineContext) -> None:
        """
        Execute the wrapped task.

        Override this in subclasses to add behavior before/after execution.

        Args:
            context: Pipeline context
        """
        self._wrapped.execute(context)
