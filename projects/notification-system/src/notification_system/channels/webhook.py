"""
Webhook channel for sending notifications via HTTP POST.
Pattern: Template Method (concrete implementation)
"""

from datetime import datetime
from typing import Any, Dict

import requests

from ..core.exceptions import (ConnectionError, InvalidRecipientError,
                               ValidationError)
from ..core.notification import Notification
from .base import NotificationChannel


class WebhookChannel(NotificationChannel):
    """
    Webhook notification channel.

    Config parameters:
    - timeout: int (optional, default=30) - request timeout in seconds
    - verify_ssl: bool (optional, default=True) - verify SSL certificates
    - headers: dict (optional) - additional HTTP headers
    - auth_token: str (optional) - Bearer token for authorization
    """

    def validate_notification(self, notification: Notification) -> None:
        """Validate notification for webhook channel."""
        if not notification.body or not notification.body.strip():
            raise ValidationError("Notification body cannot be empty for webhook.")
        if not notification.recipients or len(notification.recipients) == 0:
            raise ValidationError("At least one recipient URL is required for webhook.")
        for url in notification.recipients:
            if not (url.startswith("http://") or url.startswith("https://")):
                raise InvalidRecipientError(
                    f"Invalid URL recipient: {url}", channel="webhook"
                )

    def prepare_message(self, notification: Notification) -> Dict[str, Any]:
        """Prepare the JSON payload for the webhook."""
        message = {
            "notification_id": notification.notification_id,
            "event_id": notification.event_id,
            "body": notification.body,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": notification.metadata or {},
            "recipients": notification.recipients,
        }
        if notification.subject:
            message["subject"] = notification.subject
        # For Slack compatibility, include 'text' field
        message["text"] = notification.body
        return message

    def send_message(self, message: Dict[str, Any], connection: Any) -> Dict[str, Any]:
        """Send the message via HTTP POST to each recipient URL."""
        response_codes = []
        response_times = []
        errors = []

        for url in message.get("recipients", []):
            headers = self._build_headers()
            timeout = self.config.get("timeout", 30)
            verify_ssl = self.config.get("verify_ssl", True)

            try:
                start_time = datetime.utcnow()
                response = connection.post(
                    url,
                    json=message,
                    headers=headers,
                    timeout=timeout,
                    verify=verify_ssl,
                )
                duration = (datetime.utcnow() - start_time).total_seconds() * 1000
                response_times.append(duration)
                response_codes.append(response.status_code)

                # Check response status but don't raise yet - collect all errors
                if not (200 <= response.status_code < 300):
                    error_msg = f"HTTP {response.status_code} for {url}"
                    errors.append(error_msg)
                    self.logger.warning(error_msg)

            except requests.exceptions.Timeout:
                errors.append(f"Timeout for {url}")
                response_codes.append(0)  # Indicate failure
            except requests.exceptions.RequestException as e:
                errors.append(f"Connection error for {url}: {str(e)}")
                response_codes.append(0)

        # After trying all webhooks, check if any succeeded
        if all(code == 0 or code >= 400 for code in response_codes):
            # All failed - raise the first error
            raise ConnectionError(
                f"All webhooks failed. Errors: {'; '.join(errors)}", channel="webhook"
            )

        avg_response_time = (
            (sum(response_times) / len(response_times)) if response_times else 0
        )
        return {
            "webhook_urls": message.get("recipients", []),
            "response_codes": response_codes,
            "response_time_ms": avg_response_time,
            "errors": errors if errors else None,
            "success_count": sum(1 for code in response_codes if 200 <= code < 300),
            "total_count": len(message.get("recipients", [])),
        }

    def create_connection(self) -> Any:
        """Create a requests.Session for HTTP connections."""
        session = requests.Session()
        default_headers = self.config.get("headers", {})
        if default_headers:
            session.headers.update(default_headers)
        return session

    def close_connection(self, connection: Any) -> None:
        """Close the requests.Session."""
        if connection:
            connection.close()

    def _build_headers(self) -> Dict[str, str]:
        """Build HTTP headers for the webhook request."""
        headers = {"Content-Type": "application/json"}
        config_headers = self.config.get("headers", {})
        if config_headers:
            headers.update(config_headers)
        auth_token = self.config.get("auth_token")
        if auth_token:
            headers["Authorization"] = f"Bearer {auth_token}"
        return headers
