"""Retry decorator for automatic retry logic."""

import time
from typing import Callable, Optional

from pipeline_framework.core.models import ProcessingContext
from pipeline_framework.core.processor import Processor
from pipeline_framework.decorators.base import ProcessorDecorator


class RetryDecorator(ProcessorDecorator):
    """
    Decorator that adds retry logic to a processor.
    """

    def __init__(
        self,
        wrapped: Processor,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        backoff_multiplier: float = 2.0,
        retry_on: Optional[Callable[[Exception], bool]] = None,
        name: Optional[str] = None,
    ):
        """
        Initialize retry decorator.

        Args:
            wrapped: Processor to wrap
            max_retries: Maximum number of retry attempts
            retry_delay: Initial delay between retries (seconds)
            backoff_multiplier: Multiply delay by this after each retry
            retry_on: Optional function to determine if should retry based on exception
            name: Optional decorator name
        """
        super().__init__(wrapped, name or f"Retry({wrapped.name})")
        self._max_retries = max_retries
        self._retry_delay = retry_delay
        self._backoff_multiplier = backoff_multiplier
        self._retry_on = retry_on or (lambda e: True)

    def _do_process(self, context: ProcessingContext) -> ProcessingContext:
        """
        Process with retry logic.
        """
        attempts = 0
        delay = self._retry_delay

        while attempts <= self._max_retries:
            try:
                if attempts > 0:
                    context.data.add_metadata("retry_count", attempts)
                return self.wrapped._do_process(context)
            except Exception as e:
                attempts += 1
                if attempts > self._max_retries or not self._retry_on(e):
                    raise
                time.sleep(delay)
                delay *= self._backoff_multiplier

        return context  # This line should never be reached
