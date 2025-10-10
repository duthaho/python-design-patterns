"""
Retry decorator with exponential backoff.
Pattern: Decorator Pattern (pure composition)
"""

import logging
import time
from typing import Any

from ..channels.base import ChannelProtocol
from ..core.exceptions import PermanentError, RetriableError
from ..core.notification import Notification, NotificationResult


class RetryDecorator:
    """
    Adds automatic retry with exponential backoff.

    Only retries on RetriableError exceptions.
    PermanentError and other exceptions fail immediately.
    """

    def __init__(
        self,
        wrapped: ChannelProtocol,
        max_retries: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        backoff_multiplier: float = 2.0,
    ):
        """Initialize retry decorator."""
        self.wrapped = wrapped
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.backoff_multiplier = backoff_multiplier
        self.logger = logging.getLogger(self.__class__.__name__)

    def send(self, notification: Notification) -> NotificationResult:
        """Send with retry logic."""
        last_error = None

        for attempt in range(self.max_retries + 1):
            try:
                result = self.wrapped.send(notification)
                if result.success:
                    if attempt > 0:
                        self.logger.info(
                            f"Notification {notification.notification_id} succeeded "
                            f"after {attempt} retries"
                        )
                    return result
                else:
                    # Send returned failure without exception
                    self.logger.error(
                        f"Notification {notification.notification_id} failed "
                        f"without exception"
                    )
                    return result

            except RetriableError as e:
                last_error = e
                self.logger.warning(
                    f"Retriable error on attempt {attempt + 1}/{self.max_retries + 1} "
                    f"for notification {notification.notification_id}: {str(e)}"
                )

                # Only increment retry counter if we're going to retry
                if attempt < self.max_retries:
                    notification.increment_retry()
                    delay = self._calculate_delay(attempt)
                    self.logger.info(
                        f"Retrying notification {notification.notification_id} "
                        f"in {delay:.2f}s (attempt {attempt + 2}/{self.max_retries + 1})"
                    )
                    time.sleep(delay)
                else:
                    self.logger.error(
                        f"Max retries ({self.max_retries}) exhausted for "
                        f"notification {notification.notification_id}"
                    )

            except PermanentError as e:
                self.logger.error(
                    f"Permanent error for notification {notification.notification_id}: {str(e)}"
                )
                return NotificationResult(
                    success=False,
                    channel=self.wrapped.__class__.__name__,
                    message=f"Permanent error: {str(e)}",
                    sent_at=None,
                    metadata={"error_type": "permanent", "attempt": attempt + 1},
                )

            except Exception as e:
                self.logger.error(
                    f"Unexpected error for notification {notification.notification_id}: {str(e)}",
                    exc_info=True,
                )
                return NotificationResult(
                    success=False,
                    channel=self.wrapped.__class__.__name__,
                    message=f"Unexpected error: {str(e)}",
                    sent_at=None,
                    metadata={"error_type": "unexpected", "attempt": attempt + 1},
                )

        # All retries exhausted
        return NotificationResult(
            success=False,
            channel=self.wrapped.__class__.__name__,
            message=f"Failed after {self.max_retries} retries: {str(last_error)}",
            sent_at=None,
            metadata={
                "final_error": str(last_error),
                "total_attempts": self.max_retries + 1,
            },
        )

    def _calculate_delay(self, attempt: int) -> float:
        """Calculate exponential backoff delay."""
        delay = self.initial_delay * (self.backoff_multiplier**attempt)
        return min(delay, self.max_delay)

    def __getattr__(self, name: str) -> Any:
        """Delegate attribute access to wrapped object."""
        return getattr(self.wrapped, name)

    def __repr__(self) -> str:
        return f"RetryDecorator(wrapped={self.wrapped}, max_retries={self.max_retries})"
