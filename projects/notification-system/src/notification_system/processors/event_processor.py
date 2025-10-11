"""
Event processor that handles event-to-notification flow.
Pattern: Observer + Mediator
"""

import logging
from typing import Any, Dict, List

from ..core.event import Event
from ..core.notification import Notification, NotificationResult
from ..factories.channel_factory import ChannelFactory
from .notification_mapper import NotificationMapper


class EventProcessor:
    """
    Processes events and sends notifications.

    Pattern: Observer - observes events and triggers notifications
    Pattern: Mediator - coordinates between events, mapper, and channels
    """

    def __init__(
        self, channel_factory: ChannelFactory, notification_mapper: NotificationMapper
    ):
        """Initialize event processor."""
        self.channel_factory = channel_factory
        self.notification_mapper = notification_mapper
        self.logger = logging.getLogger(self.__class__.__name__)
        self.results: List[NotificationResult] = []

    def process_event(self, event: Event) -> List[NotificationResult]:
        """Process an event and send notifications."""
        self.logger.info(f"Processing event {event.event_id} of type {event.event_type}")

        notifications = self.notification_mapper.map_event_to_notifications(event)
        self.logger.info(f"Mapped event to {len(notifications)} notifications")

        results_for_event: List[NotificationResult] = []

        for notification in notifications:
            try:
                self.logger.info(f"Sending to channel {notification.channel}")
                channel = self.channel_factory.create(notification.channel)
                result = channel.send(notification)
                self.results.append(result)
                results_for_event.append(result)

                if result.success:
                    self.logger.info(
                        f"Notification sent successfully via {notification.channel}"
                    )
                else:
                    self.logger.warning(
                        f"Notification failed via {notification.channel}: {result.message}"
                    )

            except Exception as e:
                self.logger.error(f"Failed to send notification: {e}")
                result = NotificationResult(
                    success=False,
                    channel=notification.channel,
                    message=str(e),
                    metadata={"event_id": event.event_id},
                )
                self.results.append(result)
                results_for_event.append(result)

        success_count = sum(1 for r in results_for_event if r.success)
        total = len(results_for_event)
        self.logger.info(
            f"Processed event {event.event_id}: {success_count}/{total} successful"
        )

        return results_for_event

    def get_results(self) -> List[NotificationResult]:
        """Get all notification results."""
        return self.results

    def clear_results(self) -> None:
        """Clear stored results."""
        self.results = []

    def get_success_count(self) -> int:
        """Count successful notifications."""
        return sum(1 for r in self.results if r.success)

    def get_failure_count(self) -> int:
        """Count failed notifications."""
        return sum(1 for r in self.results if not r.success)

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"EventProcessor("
            f"total={len(self.results)}, "
            f"success={self.get_success_count()}, "
            f"failed={self.get_failure_count()})"
        )
