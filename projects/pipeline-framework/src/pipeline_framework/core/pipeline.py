"""Pipeline class implementing Chain of Responsibility pattern."""

import logging
from typing import Any, Dict, List, Optional

from ..events.event import EventType, PipelineEvent
from ..events.listener import PipelineListener
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
        self._listeners: List[PipelineListener] = []

    def add_listener(self, listener: PipelineListener) -> "Pipeline":
        """
        Add an event listener to the pipeline.

        Args:
            listener: Listener to add

        Returns:
            Self for method chaining
        """
        self._listeners.append(listener)
        return self

    def remove_listener(self, listener: PipelineListener) -> None:
        """
        Remove an event listener from the pipeline.

        Args:
            listener: Listener to remove
        """
        try:
            self._listeners.remove(listener)
        except ValueError:
            logger.warning("Listener not found in the pipeline's listener list.")

    def _emit_event(
        self,
        event_type: EventType,
        task_name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Emit an event to all registered listeners.

        Args:
            event_type: Type of event to emit
            task_name: Name of task (for task events)
            metadata: Additional event data
        """
        event = PipelineEvent(
            event_type=event_type,
            pipeline_name=self.name,
            task_name=task_name,
            metadata=metadata,
        )

        for listener in self._listeners:
            try:
                listener.on_event(event)
            except Exception as e:
                logger.error(f"Error in listener {listener}: {e}")

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

        self._emit_event(EventType.PIPELINE_STARTED)

        for task in self._tasks:
            self._emit_event(EventType.TASK_STARTED, task_name=task.name)
            try:
                task.execute(context)
                self._emit_event(EventType.TASK_COMPLETED, task_name=task.name)
            except Exception as e:
                self._emit_event(
                    EventType.TASK_FAILED, task_name=task.name, metadata={"error": str(e)}
                )
                self._emit_event(
                    EventType.PIPELINE_FAILED, metadata={"error": str(e), "failed_task": task.name}
                )
                raise TaskExecutionError(task.name, e) from e

        self._emit_event(EventType.PIPELINE_COMPLETED)
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
