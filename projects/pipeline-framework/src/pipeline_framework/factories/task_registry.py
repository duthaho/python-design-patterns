"""Registry for managing task types."""

import logging
from typing import Dict, Optional, Type

from ..core.task import Task
from .exceptions import TaskRegistrationException

logger = logging.getLogger(__name__)


class TaskRegistry:
    """
    Registry for storing and retrieving task types (Registry Pattern).

    Maintains a mapping of task type names to task classes.
    """

    def __init__(self):
        """Initialize empty registry."""
        self._registry: Dict[str, Type[Task]] = {}

    def register(self, task_type: str, task_class: Type[Task], override: bool = False) -> None:
        """
        Register a task class with a type name.

        Args:
            task_type: String identifier for the task type
            task_class: The Task class to register
            override: If True, allow overriding existing registrations

        Raises:
            TaskRegistrationException: If task_type already registered and override=False
            TaskRegistrationException: If task_class is not a Task subclass
        """
        if not issubclass(task_class, Task):
            raise TaskRegistrationException(
                f"task_class must be a subclass of Task, got {task_class}"
            )

        if not override and task_type in self._registry:
            raise TaskRegistrationException(
                f"Task type '{task_type}' is already registered. Use override=True to replace."
            )

        self._registry[task_type] = task_class
        logger.info(f"Registered task type '{task_type}' with class {task_class}")

    def unregister(self, task_type: str) -> None:
        """
        Unregister a task type.

        Args:
            task_type: The task type to unregister
        """
        self._registry.pop(task_type, None)

    def get(self, task_type: str) -> Optional[Type[Task]]:
        """
        Get a task class by type name.

        Args:
            task_type: The task type to retrieve

        Returns:
            The Task class, or None if not found
        """
        return self._registry.get(task_type)

    def has(self, task_type: str) -> bool:
        """
        Check if a task type is registered.

        Args:
            task_type: The task type to check

        Returns:
            True if registered, False otherwise
        """
        return task_type in self._registry

    def get_all_types(self) -> list[str]:
        """
        Get all registered task type names.

        Returns:
            List of registered task type names
        """
        return list(self._registry.keys())

    def clear(self) -> None:
        """Clear all registrations."""
        self._registry.clear()

    def __len__(self) -> int:
        """Return number of registered task types."""
        return len(self._registry)

    def __contains__(self, task_type: str) -> bool:
        """Check if task type is registered (enables 'in' operator)."""
        return task_type in self._registry
