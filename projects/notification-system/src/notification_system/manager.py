"""
NotificationManager - High-level facade for the notification system.
Pattern: Facade - provides simple interface to complex subsystem
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

from .config.settings import Settings
from .core.event import Event, EventPriority
from .core.notification import Notification, NotificationResult
from .factories.channel_factory import ChannelFactory
from .processors.event_processor import EventProcessor
from .processors.notification_mapper import NotificationMapper


class NotificationManager:
    """
    High-level API for sending notifications.

    Facade Pattern: Simplifies interaction with the notification system.

    Usage:
        # Initialize from config
        manager = NotificationManager.from_config()

        # Send via event (mapped to channels)
        manager.send_event(
            'user.signup',
            username='john',
            email='john@example.com'
        )

        # Send direct notification (single channel)
        manager.send_notification(
            channel='email',
            recipients=['user@example.com'],
            subject='Hello',
            body='World'
        )
    """

    def __init__(
        self,
        channel_factory: ChannelFactory,
        event_processor: EventProcessor,
        notification_mapper: NotificationMapper,
    ):
        """Initialize notification manager."""
        self.channel_factory = channel_factory
        self.event_processor = event_processor
        self.notification_mapper = notification_mapper
        self.logger = logging.getLogger(self.__class__.__name__)

    def send_event(
        self,
        event_type: str,
        user_id: Optional[str] = None,
        priority: str = "normal",
        **data,
    ) -> List[NotificationResult]:
        """Send notifications for an event."""
        self.logger.info(f"Sending event: {event_type}")

        priority_map = {
            "low": EventPriority.LOW,
            "normal": EventPriority.MEDIUM,
            "medium": EventPriority.MEDIUM,
            "high": EventPriority.HIGH,
            "critical": EventPriority.CRITICAL,
        }
        priority_enum = priority_map.get(priority.lower(), EventPriority.MEDIUM)

        event = Event(
            event_type=event_type,
            payload=data,
            user_id=user_id,
            priority=priority_enum,
        )
        results = self.event_processor.process_event(event)

        self.logger.info(
            f"Event {event_type} processed: {len(results)} notifications sent"
        )

        return results

    def send_notification(
        self,
        channel: str,
        recipients: List[str],
        body: str,
        subject: Optional[str] = None,
        event_id: Optional[str] = None,
        **kwargs,
    ) -> NotificationResult:
        """Send a direct notification (bypass event system)."""
        self.logger.info(f"Sending direct notification to {channel}")

        notification = Notification(
            event_id=event_id or str(uuid4()),
            channel=channel,
            recipients=recipients,
            subject=subject,
            body=body,
            metadata={"direct": True},
        )
        ch = self.channel_factory.create(channel)
        result = ch.send(notification)
        self.event_processor.results.append(result)

        if result.success:
            self.logger.info(f"Notification sent successfully via {channel}")
        else:
            self.logger.warning(f"Notification failed via {channel}: {result.message}")
        return result

    def get_statistics(self) -> Dict[str, Any]:
        """Get notification statistics."""
        results = self.event_processor.get_results()
        total_sent = len(results)
        successful = sum(1 for r in results if r.success)
        failed = total_sent - successful
        success_rate = (successful / total_sent * 100) if total_sent > 0 else 0.0

        stats = {
            "total_sent": total_sent,
            "successful": successful,
            "failed": failed,
            "success_rate": success_rate,
        }
        return stats

    def list_available_channels(self) -> List[str]:
        """List available channels."""
        return self.channel_factory.list_channels()

    def list_configured_events(self) -> List[str]:
        """List configured event types."""
        return self.notification_mapper.list_events()

    def clear_history(self) -> None:
        """Clear notification history."""
        self.event_processor.clear_results()

    @classmethod
    def from_config(
        cls,
        channels_config_path: str = "config/channels.yaml",
        events_config_path: str = "config/events.yaml",
    ) -> "NotificationManager":
        """Create NotificationManager from configuration files."""
        channel_settings = Settings(config_path=channels_config_path)
        channel_factory = ChannelFactory(settings=channel_settings)

        event_settings = Settings(config_path=events_config_path)
        notification_mapper = NotificationMapper(settings=event_settings)

        event_processor = EventProcessor(
            channel_factory=channel_factory,
            notification_mapper=notification_mapper,
        )

        return cls(
            channel_factory=channel_factory,
            event_processor=event_processor,
            notification_mapper=notification_mapper,
        )

    def __repr__(self) -> str:
        """String representation."""
        channels = self.list_available_channels()
        events = self.list_configured_events()
        return (
            f"NotificationManager("
            f"channels={len(channels)}, "
            f"events={len(events)})"
        )
