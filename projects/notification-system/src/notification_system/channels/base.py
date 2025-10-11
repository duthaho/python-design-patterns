"""
Abstract base class for all notification channels.
Pattern: Template Method + Strategy
"""

import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, Protocol, runtime_checkable

from ..core.notification import Notification, NotificationResult


@runtime_checkable
class ChannelProtocol(Protocol):
    """Structural interface for channels and decorators."""

    def send(self, notification: Notification) -> NotificationResult: ...
    def close(self) -> None: ...
    def health_check(self) -> bool: ...


class NotificationChannel(ABC):
    """
    Abstract base class for notification channels.

    Template Method pattern:
    - send() orchestrates the sending process
    - Subclasses implement specific steps

    Strategy pattern:
    - Each channel is a different strategy for sending notifications
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        self._connection = None

    def send(self, notification: Notification) -> NotificationResult:
        """Template method - defines the algorithm skeleton."""
        self.logger.info(
            f"Sending notification {notification.notification_id} via {self.__class__.__name__}"
        )
        try:
            self.validate_notification(notification)
            self._ensure_connection()
            message = self.prepare_message(notification)
            response_metadata = self.send_message(message, self._connection)
            result = NotificationResult(
                success=True,
                channel=notification.channel,
                message="Notification sent successfully",
                sent_at=datetime.utcnow(),
                metadata=response_metadata,
            )
            notification.mark_sent(result)
            self.logger.info(
                f"Notification {notification.notification_id} sent successfully"
            )
            return result
        except Exception as e:
            error_msg = str(e)
            self.logger.error(
                f"Failed to send notification {notification.notification_id}: {error_msg}"
            )
            result = NotificationResult(
                success=False,
                channel=notification.channel,
                message=error_msg,
                sent_at=None,
                metadata={},
            )
            notification.mark_failed(error_msg)
            return result

    @abstractmethod
    def validate_notification(self, notification: Notification) -> None:
        """Validate notification is suitable for this channel."""
        pass

    @abstractmethod
    def prepare_message(self, notification: Notification) -> Dict[str, Any]:
        """Prepare the message in channel-specific format."""
        pass

    @abstractmethod
    def send_message(self, message: Dict[str, Any], connection: Any) -> Dict[str, Any]:
        """Actually send the message using the connection."""
        pass

    @abstractmethod
    def create_connection(self) -> Any:
        """Create a new connection to the notification provider."""
        pass

    @abstractmethod
    def close_connection(self, connection: Any) -> None:
        """Close/cleanup a connection."""
        pass

    def _ensure_connection(self) -> None:
        """Ensure there is an active connection."""
        if self._connection is None:
            self._connection = self.create_connection()

    def health_check(self) -> bool:
        """Check if the channel is healthy/operational."""
        try:
            self._ensure_connection()
            return True
        except Exception as e:
            self.logger.warning(
                f"Health check failed for {self.__class__.__name__}: {e}"
            )
            return False

    def close(self) -> None:
        """Close the channel and cleanup resources."""
        if self._connection is not None:
            self.close_connection(self._connection)
            self._connection = None

    def __enter__(self):
        """Support context manager: with channel:"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Cleanup when exiting context manager"""
        self.close()

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(config_keys={list(self.config.keys())})"
