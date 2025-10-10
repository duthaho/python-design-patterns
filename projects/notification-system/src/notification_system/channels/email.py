"""
Email channel for sending notifications via SMTP.
Pattern: Template Method (concrete implementation)
"""

import html
import re
import smtplib
import uuid
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Dict

from ..core.exceptions import (AuthenticationError, ConnectionError,
                               InvalidRecipientError, ValidationError)
from ..core.notification import Notification
from .base import NotificationChannel


class EmailChannel(NotificationChannel):
    """
    Email notification channel via SMTP.

    Config parameters (all required):
    - smtp_host: str - SMTP server hostname
    - smtp_port: int - SMTP server port (587 for TLS, 465 for SSL)
    - username: str - SMTP username
    - password: str - SMTP password
    - from_email: str - Sender email address
    - use_tls: bool (optional, default=True) - Use STARTTLS
    """

    EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")

    def validate_notification(self, notification: Notification) -> None:
        """Validate notification for email channel."""
        if not notification.subject or not notification.subject.strip():
            raise ValidationError("Email subject cannot be empty.")
        if not notification.body or not notification.body.strip():
            raise ValidationError("Email body cannot be empty.")
        if not notification.recipients or len(notification.recipients) == 0:
            raise ValidationError("At least one recipient is required for email.")
        for email in notification.recipients:
            if not self._validate_email(email):
                raise InvalidRecipientError(
                    f"Invalid email address: {email}", channel="email"
                )

    def prepare_message(self, notification: Notification) -> Dict[str, Any]:
        """Prepare the MIME email message."""
        mime = MIMEMultipart("alternative")
        mime["From"] = self.config["from_email"]
        mime["To"] = ", ".join(notification.recipients)
        mime["Subject"] = notification.subject
        mime["Message-ID"] = f"<{uuid.uuid4()}@{self.config['smtp_host']}>"

        # Attach plain text body
        mime.attach(MIMEText(notification.body, "plain"))

        # Optionally attach HTML body if provided
        html_body = notification.body
        if not ("<html" in html_body.lower() or "<body" in html_body.lower()):
            # Escape HTML characters, then replace newlines
            escaped_body = html.escape(notification.body).replace("\n", "<br>")
            html_body = f"""
            <html>
                <body>
                    <div style="font-family: Arial, sans-serif;">
                        {escaped_body}
                    </div>
                </body>
            </html>
            """
        mime.attach(MIMEText(html_body, "html"))

        return {
            "mime_message": mime,
            "recipients": notification.recipients,
            "from_email": self.config["from_email"],
        }

    def send_message(self, message: Dict[str, Any], connection: Any) -> Dict[str, Any]:
        """Send the email via the SMTP connection."""
        try:
            connection.send_message(message["mime_message"])
            return {
                "message_id": message["mime_message"]["Message-ID"],
                "recipients": message["recipients"],
                "from_email": message["from_email"],
                "status": "sent",
            }
        except smtplib.SMTPAuthenticationError as e:
            raise AuthenticationError(
                "SMTP authentication failed", channel="email"
            ) from e
        except smtplib.SMTPRecipientsRefused as e:
            raise InvalidRecipientError(
                "One or more recipient addresses were refused",
                channel="email",
            ) from e
        except smtplib.SMTPException as e:
            raise ConnectionError(
                f"SMTP error occurred: {str(e)}", channel="email"
            ) from e

    def create_connection(self) -> smtplib.SMTP:
        """Create and return an SMTP connection."""
        try:
            host = self.config["smtp_host"]
            port = self.config["smtp_port"]
            username = self.config["username"]
            password = self.config["password"]
            use_tls = self.config.get("use_tls", True)

            connection = smtplib.SMTP(host, port, timeout=10)
            connection.ehlo()
            if use_tls:
                connection.starttls()
                connection.ehlo()
            connection.login(username, password)
            return connection
        except smtplib.SMTPAuthenticationError as e:
            raise AuthenticationError(
                "SMTP authentication failed", channel="email"
            ) from e
        except (smtplib.SMTPConnectError, smtplib.SMTPServerDisconnected) as e:
            raise ConnectionError("Failed to connect to SMTP server") from e
        except Exception as e:
            raise ConnectionError(f"Unexpected error occurred: {str(e)}") from e

    def close_connection(self, connection: Any) -> None:
        """Close the SMTP connection."""
        try:
            if connection:
                connection.quit()
        except Exception as e:
            self.logger.warning(f"Error closing SMTP connection: {str(e)}")

    @staticmethod
    def _validate_email(email: str) -> bool:
        """
        Helper: Validate email format.
        """
        return bool(EmailChannel.EMAIL_REGEX.match(email))
