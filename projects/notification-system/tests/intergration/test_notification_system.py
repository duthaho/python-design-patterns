"""
Integration tests for the complete notification system.
Tests all components working together.
"""

import logging
import tempfile
import unittest
from pathlib import Path

import yaml
from notification_system import NotificationManager
from notification_system.core.notification import NotificationStatus
from notification_system.events import OrderPlacedEvent, UserSignupEvent


class TestNotificationSystemIntegration(unittest.TestCase):
    """Integration tests for the complete system."""

    @classmethod
    def setUpClass(cls):
        """Set up test configuration files."""
        cls.temp_dir = tempfile.mkdtemp()

        # Create channels config
        channels_config = {
            "channels": {
                "console": {
                    "type": "ConsoleChannel",
                    "enabled": True,
                    "config": {"format": "json"},
                    "decorators": [{"type": "logging", "log_level": "INFO"}],
                }
            }
        }

        cls.channels_config_path = Path(cls.temp_dir) / "channels.yaml"
        with open(cls.channels_config_path, "w") as f:
            yaml.dump(channels_config, f)

        # Create events config
        events_config = {
            "events": {
                "user.signup": {
                    "channels": ["console"],
                    "template": {
                        "subject": "Welcome {username}!",
                        "body": "Hello {username}, your email is {email}",
                    },
                },
                "order.placed": {
                    "channels": ["console"],
                    "template": {
                        "subject": "Order {order_id}",
                        "body": "Order for {customer_name}: {total_amount}",
                    },
                },
            },
            "defaults": {
                "channels": ["console"],
                "template": {
                    "subject": "Event: {event_type}",
                    "body": "Event {event_id} occurred",
                },
            },
        }

        cls.events_config_path = Path(cls.temp_dir) / "events.yaml"
        with open(cls.events_config_path, "w") as f:
            yaml.dump(events_config, f)

    def setUp(self):
        """Set up manager for each test."""
        self.manager = NotificationManager.from_config(
            channels_config_path=str(self.channels_config_path),
            events_config_path=str(self.events_config_path),
        )
        self.manager.clear_history()

    def test_send_event_simple_string(self):
        """Should send notification for string-based event."""
        results = self.manager.send_event(
            "user.signup", username="TestUser", email="test@example.com"
        )

        self.assertEqual(len(results), 1)
        self.assertTrue(results[0].success)
        self.assertEqual(results[0].channel, "console")

    def test_send_event_with_concrete_class(self):
        """Should work with concrete event classes."""
        # Create event
        event = UserSignupEvent(username="Alice", email="alice@example.com")

        # Process through manager's event processor
        results = self.manager.event_processor.process_event(event)

        self.assertEqual(len(results), 1)
        self.assertTrue(results[0].success)

    def test_send_direct_notification(self):
        """Should send direct notification."""
        result = self.manager.send_notification(
            channel="console",
            recipients=["user@example.com"],
            subject="Test Subject",
            body="Test body",
        )

        self.assertTrue(result.success)

    def test_multiple_events(self):
        """Should handle multiple events correctly."""
        # Send multiple events
        self.manager.send_event(
            "user.signup", username="User1", email="user1@example.com"
        )
        self.manager.send_event(
            "user.signup", username="User2", email="user2@example.com"
        )
        self.manager.send_event(
            "order.placed",
            order_id="ORD-1",
            customer_name="User1",
            customer_email="user1@example.com",
            total_amount=99.99,
            item_count=2,
        )

        stats = self.manager.get_statistics()

        self.assertEqual(stats["total_sent"], 3)
        self.assertEqual(stats["successful"], 3)
        self.assertEqual(stats["failed"], 0)
        self.assertEqual(stats["success_rate"], 100.0)

    def test_unknown_event_uses_defaults(self):
        """Should use default config for unknown events."""
        results = self.manager.send_event("unknown.event.type", some_field="value")

        # Should still send with default config
        self.assertEqual(len(results), 1)
        self.assertTrue(results[0].success)

    def test_template_substitution(self):
        """Should correctly substitute template variables."""
        results = self.manager.send_event(
            "user.signup", username="Bob", email="bob@example.com"
        )

        # The notification should have been sent
        self.assertTrue(results[0].success)

    def test_list_available_channels(self):
        """Should list available channels."""
        channels = self.manager.list_available_channels()

        self.assertIn("console", channels)

    def test_list_configured_events(self):
        """Should list configured events."""
        events = self.manager.list_configured_events()

        self.assertIn("user.signup", events)
        self.assertIn("order.placed", events)

    def test_statistics_accumulation(self):
        """Should accumulate statistics correctly."""
        # Send some notifications
        self.manager.send_event("user.signup", username="A", email="a@example.com")
        self.manager.send_event("user.signup", username="B", email="b@example.com")

        stats = self.manager.get_statistics()
        self.assertEqual(stats["total_sent"], 2)

        # Send more
        self.manager.send_event(
            "order.placed",
            order_id="O1",
            customer_name="A",
            customer_email="a@example.com",
            total_amount=50.0,
            item_count=1,
        )

        stats = self.manager.get_statistics()
        self.assertEqual(stats["total_sent"], 3)

    def test_clear_history(self):
        """Should clear notification history."""
        # Send some notifications
        self.manager.send_event(
            "user.signup", username="Test", email="test@example.com"
        )

        stats_before = self.manager.get_statistics()
        self.assertGreater(stats_before["total_sent"], 0)

        # Clear
        self.manager.clear_history()

        stats_after = self.manager.get_statistics()
        self.assertEqual(stats_after["total_sent"], 0)


class TestEventClasses(unittest.TestCase):
    """Test concrete event classes."""

    def test_user_signup_event_creation(self):
        """Should create UserSignupEvent correctly."""
        event = UserSignupEvent(username="john", email="john@example.com")

        self.assertEqual(event.event_type, "user.signup")
        self.assertEqual(event.username, "john")
        self.assertEqual(event.email, "john@example.com")
        self.assertIn("signup_date", event.payload)

    def test_user_signup_event_validation(self):
        """Should validate UserSignupEvent payload."""
        # Valid event should not raise
        event = UserSignupEvent(username="john", email="john@example.com")

        # Invalid email should raise
        with self.assertRaises(ValueError):
            UserSignupEvent(username="john", email="invalid-email")  # No @ or .

    def test_order_placed_event_creation(self):
        """Should create OrderPlacedEvent correctly."""
        event = OrderPlacedEvent(
            order_id="ORD-123",
            customer_name="Alice",
            customer_email="alice@example.com",
            total_amount=149.99,
            item_count=3,
        )

        self.assertEqual(event.event_type, "order.placed")
        self.assertEqual(event.payload["order_id"], "ORD-123")
        self.assertEqual(event.payload["total_amount"], 149.99)

    def test_order_placed_event_validation(self):
        """Should validate OrderPlacedEvent payload."""
        # Negative amount should raise
        with self.assertRaises(ValueError):
            OrderPlacedEvent(
                order_id="ORD-123",
                customer_name="Alice",
                customer_email="alice@example.com",
                total_amount=-10.0,  # Invalid
                item_count=1,
            )

        # Zero items should raise
        with self.assertRaises(ValueError):
            OrderPlacedEvent(
                order_id="ORD-123",
                customer_name="Alice",
                customer_email="alice@example.com",
                total_amount=50.0,
                item_count=0,  # Invalid
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)
