"""
Logging decorator for structured logging.
Pattern: Decorator Pattern (adds logging)
"""

import logging
import time
from datetime import datetime
from typing import Any

from ..channels.base import ChannelProtocol
from ..core.notification import Notification, NotificationResult


class LoggingDecorator:
    """
    Adds structured logging to channel operations.

    Logs:
    - Send attempts (start)
    - Send results (success/failure)
    - Duration
    - Notification details

    Config parameters:
    - log_level: str (default: 'INFO') - logging level
    """

    def __init__(self, wrapped: ChannelProtocol, log_level: str = "INFO"):
        """Initialize logging decorator."""
        self.wrapped = wrapped
        self.log_level = log_level.upper()
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.setLevel(getattr(logging, self.log_level, logging.INFO))

    def send(self, notification: Notification) -> NotificationResult:
        """Send with logging."""
        self._log_send_start(notification)
        start_time = time.time()
        try:
            result = self.wrapped.send(notification)
            duration = time.time() - start_time
            self._log_send_result(notification, result, duration)
            return result
        except Exception as e:
            duration = time.time() - start_time
            self.logger.error(
                f"Notification {notification.notification_id} failed: {str(e)} "
                f"(duration: {duration:.2f}s)"
            )
            return NotificationResult(
                success=False,
                channel=self.wrapped.__class__.__name__,
                message=str(e),
                sent_at=None,
                metadata={},
            )

    def _log_send_start(self, notification: Notification) -> None:
        """Log the start of a send operation."""
        self.logger.info(
            f"Starting send for notification {notification.notification_id} "
            f"via {self.wrapped.__class__.__name__} to {notification.recipients} "
            f"(event_id: {notification.event_id}) at {datetime.utcnow().isoformat()}"
        )

    def _log_send_result(
        self, notification: Notification, result: NotificationResult, duration: float
    ) -> None:
        """Log the result of a send operation."""
        if result.success:
            self.logger.info(
                f"Notification {notification.notification_id} sent successfully "
                f"in {duration:.2f}s"
            )
        else:
            self.logger.error(
                f"Notification {notification.notification_id} failed: "
                f"{result.message} (duration: {duration:.2f}s)"
            )

    def __getattr__(self, name: str) -> Any:
        """
        Magic method: delegate any attribute access to wrapped object.

        This makes the decorator transparent - any method/attribute
        not defined in LoggingDecorator automatically delegates to wrapped.
        """
        return getattr(self.wrapped, name)

    def __repr__(self) -> str:
        return f"LoggingDecorator(wrapped={self.wrapped}, log_level={self.log_level})"
