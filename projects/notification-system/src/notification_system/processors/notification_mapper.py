"""
Maps events to notifications using configuration.
Pattern: Strategy + Template Method
"""

import logging
from typing import Any, Dict, List

from ..config.settings import ConfigurationError, Settings
from ..core.event import Event
from ..core.notification import Notification


class NotificationMapper:
    """
    Maps events to notifications based on configuration.

    Responsibilities:
    - Read event configuration
    - Determine which channels to use for an event
    - Apply templates to create notification content
    - Create Notification objects from Events
    """

    def __init__(self, settings: Settings):
        """Initialize mapper with settings."""
        self.settings = settings
        self.event_config = settings.config.get("events", {})
        self.defaults = settings.config.get("defaults", {})
        self.logger = logging.getLogger(self.__class__.__name__)

    def map_event_to_notifications(self, event: Event) -> List[Notification]:
        """Map an event to one or more notifications."""
        event_type = event.event_type
        config = self.get_event_config(event_type)
        channels = config.get("channels", ["console"])
        template = config.get("template")
        data = {
            "event_id": event.event_id,
            "event_type": event.event_type,
            "timestamp": event.timestamp.isoformat(),
            **event.payload,  # Include all payload fields
        }

        notifications = []
        for channel in channels:
            recipients = self._extract_recipients(event, channel)
            content = self._apply_template(template, data)
            notification = Notification(
                event_id=event.event_id,
                channel=channel,
                recipients=recipients,
                subject=content.get("subject"),
                body=content.get("body"),
                metadata={"event_type": event.event_type},
            )
            notifications.append(notification)
        return notifications

    def _apply_template(
        self, template: Dict[str, str], data: Dict[str, Any]
    ) -> Dict[str, str]:
        """Apply template with data substitution."""
        if template is None:
            template = {
                "subject": "Notification: {event_type}",
                "body": "Event {event_id} at {timestamp}",
            }
        subject_template = template.get("subject", "Notification: {event_type}")
        body_template = template.get("body", "Event {event_id} at {timestamp}")
        try:
            subject = subject_template.format_map(data)
            body = body_template.format_map(data)
        except KeyError as e:
            self.logger.error(f"Template substitution error: missing key {e}")
            subject = subject_template
            body = body_template
        return {"subject": subject, "body": body}

    def _extract_recipients(self, event: Event, channel: str) -> List[str]:
        """Extract recipient addresses from event based on channel type."""
        recipients = []
        payload = event.payload
        metadata = event.metadata

        if channel == "email":
            email = payload.get("email") or payload.get("customer_email")
            if email:
                recipients.append(email)
            elif event.user_id:
                recipients.append(f"{event.user_id}@example.com")
        elif channel == "webhook":
            webhook_url = metadata.get("webhook_url") or self.settings.config.get(
                "default_webhook_url"
            )
            if webhook_url:
                recipients.append(webhook_url)
            else:
                recipients.append("http://localhost:8000/webhook")
        elif channel == "console":
            if event.user_id:
                recipients.append(event.user_id)
            else:
                recipients.append("console@localhost")
        else:
            # Try to find a field in payload matching the channel name
            field_value = payload.get(channel)
            if field_value:
                if isinstance(field_value, list):
                    recipients.extend(field_value)
                else:
                    recipients.append(str(field_value))
        if not recipients:
            raise ConfigurationError(
                f"Cannot determine recipients for channel '{channel}' in event '{event.event_id}'"
            )
        return recipients

    def get_event_config(self, event_type: str) -> Dict[str, Any]:
        """Get configuration for a specific event type."""
        if event_type in self.event_config:
            return self.event_config[event_type]
        else:
            return {
                "channels": self.defaults.get("channels", ["console"]),
                "priority": self.defaults.get("priority", "normal"),
                "template": self.defaults.get("template"),
            }

    def list_events(self) -> List[str]:
        """List all configured event types."""
        return list(self.event_config.keys())

    def __repr__(self) -> str:
        """String representation."""
        return f"NotificationMapper(events={len(self.event_config)})"
