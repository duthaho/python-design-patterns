"""Timeout decorator for limiting task execution time."""

import logging
import threading

from ..core.context import PipelineContext
from ..core.task import Task
from .base import TaskDecorator

logger = logging.getLogger(__name__)


class TimeoutException(Exception):
    """Raised when task execution times out."""

    pass


class TimeoutDecorator(TaskDecorator):
    """
    Decorator that enforces a timeout on task execution.

    Note: Uses signal.alarm() which only works on Unix systems.
    For cross-platform support, consider using threading.Timer.
    """

    def __init__(self, wrapped_task: Task, timeout: int):
        """
        Initialize timeout decorator.

        Args:
            wrapped_task: Task to wrap
            timeout: Maximum execution time in seconds
        """
        super().__init__(wrapped_task)
        self.timeout = timeout

    def _timeout_handler(self, signum, frame):
        """Signal handler for timeout."""
        raise TimeoutException(f"Task {self.name} timed out after {self.timeout}s")

    def execute(self, context: PipelineContext) -> None:
        """
        Execute with timeout.

        Args:
            context: Pipeline context

        Raises:
            TimeoutException: If execution exceeds timeout
        """
        result = [None]
        exception = [None]

        def target():
            try:
                self._wrapped.execute(context)
            except Exception as e:
                exception[0] = e

        thread = threading.Thread(target=target)
        thread.daemon = True
        thread.start()
        thread.join(timeout=self.timeout)

        if thread.is_alive():
            raise TimeoutException(...)
        if exception[0]:
            raise exception[0]
