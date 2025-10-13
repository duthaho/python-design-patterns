"""Built-in task types for common operations."""

import logging
from typing import Any, Callable

from ..core.context import PipelineContext
from ..core.task import Task

logger = logging.getLogger(__name__)


class FunctionTask(Task):
    """
    Task that wraps a simple function (Adapter Pattern).

    Allows using plain functions as tasks without creating classes.
    """

    def __init__(self, name: str, func: Callable[[PipelineContext], None], description: str = ""):
        """
        Initialize function task.

        Args:
            name: Task name
            func: Function to execute (takes context as parameter)
            description: Task description
        """
        super().__init__(name, description)
        self._func = func

    def execute(self, context: PipelineContext) -> None:
        """Execute the wrapped function."""
        self._func(context)


class LogTask(Task):
    """Task that logs a message."""

    VALID_LEVELS = {"DEBUG", "INFO", "WARNING", "ERROR"}

    def __init__(self, name: str, message: str, level: str = "INFO"):
        """
        Initialize log task.

        Args:
            name: Task name
            message: Message to log
            level: Log level (DEBUG, INFO, WARNING, ERROR)
        """
        if level.upper() not in self.VALID_LEVELS:
            raise ValueError(f"Invalid log level '{level}'. Must be one of {self.VALID_LEVELS}.")
        
        super().__init__(name, f"Log message at {level} level")
        self.message = message
        self.level = level

    def execute(self, context: PipelineContext) -> None:
        """Log the message."""
        try:
            message = self.message.format(**context.get_all())
        except KeyError as e:
            message = self.message

        getattr(logger, self.level.lower())(message)


class SetValueTask(Task):
    """Task that sets a value in the context."""

    def __init__(self, name: str, key: str, value: Any):
        """
        Initialize set value task.

        Args:
            name: Task name
            key: Context key to set
            value: Value to set
        """
        super().__init__(name, f"Set {key} in context")
        self.key = key
        self.value = value

    def execute(self, context: PipelineContext) -> None:
        """Set the value in context."""
        context.set(self.key, self.value)
