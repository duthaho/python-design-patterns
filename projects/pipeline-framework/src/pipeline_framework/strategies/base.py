"""Base execution strategy interface with event support."""

import logging
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional

from ..core.context import PipelineContext
from ..core.task import Task

logger = logging.getLogger(__name__)


class ExecutionStrategy(ABC):
    """
    Abstract base class for task execution strategies (Strategy Pattern).

    Strategies can optionally emit events during task execution.
    """

    def __init__(self):
        """Initialize strategy."""
        self._event_callback: Optional[Callable] = None

    def set_event_callback(
        self, callback: Callable[[str, Optional[str], Optional[Dict[str, Any]]], None]
    ) -> None:
        """
        Set callback for emitting events.

        Args:
            callback: Function to call for emitting events
                     Signature: (event_type, task_name, metadata) -> None
        """
        self._event_callback = callback

    def _emit_task_event(
        self,
        event_type: str,
        task_name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Emit a task-level event if callback is set.

        Args:
            event_type: Type of event ('task_started', 'task_completed', 'task_failed')
            task_name: Name of the task
            metadata: Additional event data
        """
        if self._event_callback:
            try:
                self._event_callback(event_type, task_name, metadata)
            except Exception as e:
                logger.warning(f"Event callback failed: {e}")

    @abstractmethod
    def execute(self, tasks: List[Task], context: PipelineContext) -> None:
        """
        Execute a list of tasks using this strategy.

        Args:
            tasks: List of tasks to execute
            context: Pipeline context for data sharing

        Raises:
            Exception: If task execution fails
        """
        pass

    def get_name(self) -> str:
        """Get the name of this strategy."""
        return self.__class__.__name__
