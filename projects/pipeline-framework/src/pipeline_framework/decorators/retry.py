"""Retry decorator for automatic retry on failure."""

import logging
import time
from typing import Optional, Type

from ..core.context import PipelineContext
from ..core.task import Task
from .base import TaskDecorator

logger = logging.getLogger(__name__)


class RetryDecorator(TaskDecorator):
    """
    Decorator that retries task execution on failure.

    Implements exponential backoff between retries.
    """

    def __init__(
        self,
        wrapped_task: Task,
        max_retries: int = 3,
        delay: float = 1.0,
        backoff: float = 2.0,
        exceptions: tuple = (Exception,),
    ):
        """
        Initialize retry decorator.

        Args:
            wrapped_task: Task to wrap
            max_retries: Maximum number of retry attempts
            delay: Initial delay between retries (seconds)
            backoff: Multiplier for delay after each retry
            exceptions: Tuple of exceptions to catch and retry
        """
        super().__init__(wrapped_task)
        self.max_retries = max_retries
        self.delay = delay
        self.backoff = backoff
        self.exceptions = exceptions

    def execute(self, context: PipelineContext) -> None:
        """
        Execute with retry logic.

        Args:
            context: Pipeline context
        """
        last_exception = None
        current_delay = self.delay
        
        for attempt in range(self.max_retries + 1):
            try:
                self._wrapped.execute(context)
                return  # Success!
            except self.exceptions as e:
                last_exception = e
                if attempt < self.max_retries:
                    logger.warning(f"Task {self.name} failed (attempt {attempt + 1}), retrying in {current_delay}s...")
                    time.sleep(current_delay)
                    current_delay *= self.backoff
                else:
                    logger.error(f"Task {self.name} failed after {self.max_retries + 1} attempts")
        
        raise last_exception
