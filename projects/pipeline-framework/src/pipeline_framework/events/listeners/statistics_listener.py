"""Statistics collector listener for gathering pipeline metrics."""

from typing import Dict, List

from ..event import PipelineEvent
from ..listener import PipelineListener


class StatisticsListener(PipelineListener):
    """
    Listener that collects statistics about pipeline execution.

    Tracks:
    - Total tasks executed
    - Tasks succeeded
    - Tasks failed
    - Task names executed
    """

    def __init__(self):
        """Initialize statistics collector."""
        self.tasks_started: int = 0
        self.tasks_completed: int = 0
        self.tasks_failed: int = 0
        self.task_names: List[str] = []
        self.failed_task_names: List[str] = []

    def on_task_started(self, event: PipelineEvent) -> None:
        """Increment started counter and record task name."""
        self.task_names.append(event.task_name)
        self.tasks_started += 1

    def on_task_completed(self, event: PipelineEvent) -> None:
        """Increment completed counter."""
        self.tasks_completed += 1

    def on_task_failed(self, event: PipelineEvent) -> None:
        """Increment failed counter and record failed task name."""
        self.tasks_failed += 1
        self.failed_task_names.append(event.task_name)

    def get_statistics(self) -> Dict[str, any]:
        """
        Get collected statistics.

        Returns:
            Dictionary with statistics
        """
        return {
            "tasks_started": self.tasks_started,
            "tasks_completed": self.tasks_completed,
            "tasks_failed": self.tasks_failed,
            "success_rate": (
                self.tasks_completed / self.tasks_started if self.tasks_started > 0 else 0
            ),
            "task_names": self.task_names.copy(),
            "failed_task_names": self.failed_task_names.copy(),
        }

    def reset(self) -> None:
        """Reset all statistics to initial state."""
        self.tasks_started = 0
        self.tasks_completed = 0
        self.tasks_failed = 0
        self.task_names = []
        self.failed_task_names = []
