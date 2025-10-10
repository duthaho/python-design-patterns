"""
Unit tests for notification channels using mocks.
"""

import smtplib
import unittest
from unittest.mock import MagicMock, Mock, patch

from notification_system.channels.console import ConsoleChannel
from notification_system.channels.email import EmailChannel
from notification_system.channels.webhook import WebhookChannel
from notification_system.core.exceptions import (AuthenticationError,
                                                 InvalidRecipientError,
                                                 ValidationError)
from notification_system.core.notification import (Notification,
                                                   NotificationStatus)


class TestConsoleChannel(unittest.TestCase):
    """Test ConsoleChannel"""

    def setUp(self):
        self.channel = ConsoleChannel(config={"format": "pretty"})
        self.notification = Notification(
            event_id="evt-123",
            channel="console",
            recipients=["test@example.com"],
            subject="Test Subject",
            body="Test message body",
        )

    def test_validate_notification_success(self):
        """Should validate correct notification"""
        # Should not raise
        self.channel.validate_notification(self.notification)

    def test_validate_notification_empty_body(self):
        """Should reject empty body"""
        self.notification.body = ""
        with self.assertRaises(ValidationError):
            self.channel.validate_notification(self.notification)

    @patch("builtins.print")  # Mock print to capture output
    def test_send_message_pretty_format(self, mock_print):
        """Should print pretty formatted message"""
        result = self.channel.send(self.notification)

        self.assertTrue(result.success)
        self.assertEqual(result.channel, "ConsoleChannel")
        self.assertIsNotNone(result.sent_at)
        mock_print.assert_called()  # Verify print was called

    def test_send_message_json_format(self):
        """Should print JSON formatted message"""
        channel = ConsoleChannel(config={"format": "json"})
        result = channel.send(self.notification)

        self.assertTrue(result.success)


class TestWebhookChannel(unittest.TestCase):
    """Test WebhookChannel"""

    def setUp(self):
        self.channel = WebhookChannel(config={"timeout": 10})
        self.notification = Notification(
            event_id="evt-123",
            channel="webhook",
            recipients=["https://webhook.site/test"],
            body="Test webhook message",
        )

    def test_validate_notification_valid_url(self):
        """Should accept valid HTTPS URL"""
        self.channel.validate_notification(self.notification)

    def test_validate_notification_invalid_url(self):
        """Should reject invalid URL"""
        self.notification.recipients = ["not-a-url"]
        with self.assertRaises(InvalidRecipientError):
            self.channel.validate_notification(self.notification)

    @patch("requests.Session.post")
    def test_send_message_success(self, mock_post):
        """Should send POST request successfully"""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True}
        mock_response.elapsed.total_seconds.return_value = 0.5
        mock_post.return_value = mock_response

        result = self.channel.send(self.notification)

        self.assertTrue(result.success)
        mock_post.assert_called_once()

    @patch("requests.Session.post")
    def test_send_message_authentication_error(self, mock_post):
        """Should handle 401 authentication error"""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.raise_for_status.side_effect = Exception("401 Unauthorized")
        mock_post.return_value = mock_response

        result = self.channel.send(self.notification)

        self.assertFalse(result.success)
        self.assertEqual(self.notification.status, NotificationStatus.FAILED)


class TestEmailChannel(unittest.TestCase):
    """Test EmailChannel"""

    def setUp(self):
        self.config = {
            "smtp_host": "smtp.test.com",
            "smtp_port": 587,
            "username": "test@test.com",
            "password": "password",
            "from_email": "sender@test.com",
            "use_tls": True,
        }
        self.channel = EmailChannel(config=self.config)
        self.notification = Notification(
            event_id="evt-123",
            channel="email",
            recipients=["recipient@test.com"],
            subject="Test Email",
            body="<h1>Test</h1><p>This is a test email</p>",
        )

    def test_validate_notification_valid_email(self):
        """Should accept valid email address"""
        self.channel.validate_notification(self.notification)

    def test_validate_notification_invalid_email(self):
        """Should reject invalid email address"""
        self.notification.recipients = ["not-an-email"]

        with self.assertRaises(InvalidRecipientError) as context:
            self.channel.validate_notification(self.notification)

        # Verify the exception has the channel attribute
        self.assertEqual(context.exception.channel, "email")
        self.assertFalse(context.exception.retriable)

    def test_validate_notification_missing_subject(self):
        """Should reject missing subject"""
        self.notification.subject = None
        with self.assertRaises(ValidationError):
            self.channel.validate_notification(self.notification)

    @patch("smtplib.SMTP")
    def test_send_message_success(self, mock_smtp_class):
        """Should send email successfully"""
        # Mock SMTP instance
        mock_smtp = MagicMock()
        mock_smtp_class.return_value = mock_smtp

        result = self.channel.send(self.notification)

        self.assertTrue(result.success)
        mock_smtp.starttls.assert_called_once()
        mock_smtp.login.assert_called_once_with("test@test.com", "password")
        mock_smtp.send_message.assert_called_once()

    @patch("smtplib.SMTP")
    def test_create_connection_authentication_error(self, mock_smtp_class):
        """Should handle authentication error"""
        mock_smtp = MagicMock()
        mock_smtp.login.side_effect = smtplib.SMTPAuthenticationError(
            535, b"Authentication failed"
        )
        mock_smtp_class.return_value = mock_smtp

        with self.assertRaises(AuthenticationError):
            self.channel.create_connection()

    def test_prepare_message_html_support(self):
        """Should prepare HTML email correctly"""
        message_dict = self.channel.prepare_message(self.notification)

        self.assertIn("mime_message", message_dict)
        self.assertIn("recipients", message_dict)

        mime_msg = message_dict["mime_message"]
        # Check it's multipart
        self.assertTrue(mime_msg.is_multipart())


if __name__ == "__main__":
    unittest.main()
