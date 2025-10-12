"""Base Task class implementing Command Pattern."""

from abc import ABC, abstractmethod
from typing import Optional

from .context import PipelineContext


class Task(ABC):
    """
    Abstract base class for all pipeline tasks (Command Pattern).

    Each task encapsulates a unit of work that can be executed
    within a pipeline context.
    """

    def __init__(self, name: str, description: Optional[str] = None):
        """
        Initialize a task.

        Args:
            name: Unique name for this task
            description: Optional description of what the task does
        """
        if not name or not name.strip():
            raise ValueError("Task name must be provided and non-empty.")
        self.name = name
        self.description = description or ""

    @abstractmethod
    def execute(self, context: PipelineContext) -> None:
        """
        Execute the task logic.

        Tasks should read inputs from context and write outputs back to it.

        Args:
            context: The pipeline context for reading/writing data

        Raises:
            TaskExecutionError: If task execution fails
        """
        pass

    def __repr__(self) -> str:
        """String representation of the task."""
        return f"Task(name='{self.name}')"
