"""
Console channel for development and testing.
Prints notifications to stdout with formatting.
Pattern: Template Method (concrete implementation)
"""

import json
from datetime import datetime
from typing import Any, Dict

from ..core.exceptions import ValidationError
from ..core.notification import Notification
from .base import NotificationChannel


class ConsoleChannel(NotificationChannel):
    """
    Console notification channel for testing.

    Config parameters:
    - colored: bool (optional, default=True) - use colored output
    - format: str (optional, default='pretty') - 'pretty' or 'json'
    """

    def validate_notification(self, notification: Notification) -> None:
        """Validate notification for console channel."""
        if not notification.body or not notification.body.strip():
            raise ValidationError(
                "Notification body cannot be empty for console channel."
            )
        if not notification.recipients or len(notification.recipients) == 0:
            raise ValidationError(
                "At least one recipient is required for console channel."
            )

    def prepare_message(self, notification: Notification) -> Dict[str, Any]:
        """Prepare the message dictionary for console output."""
        message = {
            "notification_id": notification.notification_id,
            "recipients": notification.recipients,
            "subject": notification.subject if notification.subject else "",
            "body": notification.body,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": notification.metadata or {},
        }
        return message

    def send_message(self, message: Dict[str, Any], connection: Any) -> Dict[str, Any]:
        """Send the message by printing to console."""
        format_type = self.config.get("format", "pretty").lower()
        colored = self.config.get("colored", True)

        if format_type == "json":
            print(json.dumps(message, indent=2))
        else:
            # Pretty format
            pretty_message = self._format_pretty(message)
            if colored:
                # Add ANSI color codes for better visibility
                pretty_message = f"\033[92m{pretty_message}\033[0m"  # Green text
            print(pretty_message)

        return {"printed_at": datetime.utcnow().isoformat(), "format": format_type}

    def create_connection(self) -> Any:
        """No connection needed for console channel."""
        return None

    def close_connection(self, connection: Any) -> None:
        """No connection to close for console channel."""
        pass

    def _format_pretty(self, message: Dict[str, Any]) -> str:
        """Format the message in a human-readable way."""
        lines = [
            "=" * 50,
            f"📧  CONSOLE NOTIFICATION [{message['timestamp']}]",
            "=" * 50,
            f"ID: {message['notification_id']}",
            f"To: {', '.join(message['recipients'])}",
        ]
        if message["subject"]:
            lines.append(f"Subject: {message['subject']}")
        lines.append("-" * 50)
        lines.append("Body:")
        body_lines = message["body"].splitlines()
        for line in body_lines:
            lines.append(f"  {line}")
        if message.get("metadata"):
            lines.append(f"Metadata: {json.dumps(message['metadata'], indent=2)}")
        lines.append("=" * 50)
        return "\n".join(lines)
