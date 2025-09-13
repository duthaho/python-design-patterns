import heapq
import re
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Tuple


# Priority levels
class Priority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


# Implementation interface
class DeliveryProvider(ABC):
    @abstractmethod
    def send(
        self, message: str, recipient: str, metadate: Dict[str, Any] = None
    ) -> bool:
        pass

    @abstractmethod
    def validate_recipient(self, recipient: str) -> bool:
        pass


# Concrete implementations
class AWSSESProvider(DeliveryProvider):
    def send(
        self, message: str, recipient: str, metadate: Dict[str, Any] = None
    ) -> bool:
        if not self.validate_recipient(recipient):
            raise ValueError(f"Invalid email address: {recipient}")

        priority_header = (
            f"{metadate.get('priority', 'normal')}" if metadate else "normal"
        )
        print(
            f"AWS SES sending to {recipient} with priority {priority_header}: {message}"
        )
        return True

    def validate_recipient(self, recipient: str) -> bool:
        return bool(re.match(r"[^@]+@[^@]+\.[^@]+", recipient))


class TwilioSMSProvider(DeliveryProvider):
    def send(
        self, message: str, recipient: str, metadate: Dict[str, Any] = None
    ) -> bool:
        if not self.validate_recipient(recipient):
            raise ValueError(f"Invalid phone number: {recipient}")

        if len(message) > 160:
            message = message[:157] + "..."  # Truncate to 160 chars

        priority_header = (
            f"{metadate.get('priority', 'normal')}" if metadate else "normal"
        )
        print(
            f"Twilio SMS sending to {recipient} with priority {priority_header}: {message}"
        )
        return True

    def validate_recipient(self, recipient: str) -> bool:
        return bool(re.match(r"^\+?[1-9]\d{1,14}$", recipient))


class PushNotificationProvider(DeliveryProvider):
    def send(
        self, message: str, recipient: str, metadate: Dict[str, Any] = None
    ) -> bool:
        if not self.validate_recipient(recipient):
            raise ValueError(f"Invalid device token: {recipient}")

        priority_header = (
            f"{metadate.get('priority', 'normal')}" if metadate else "normal"
        )
        print(
            f"Push Notification sending to {recipient} with priority {priority_header}: {message}"
        )
        return True

    def validate_recipient(self, recipient: str) -> bool:
        return len(recipient) > 0 and recipient.isalnum()


# Abstraction
class Notification(ABC):
    def __init__(
        self,
        provider: DeliveryProvider,
        template: str,
        priority: Priority = Priority.MEDIUM,
    ):
        self.provider = provider
        self.template = template
        self.priority = priority
        self.timestamp = datetime.now()

    def send(self, recipient: str, **template_vars) -> bool:
        """Send notification to the recipient."""
        try:
            if not self.provider.validate_recipient(recipient):
                raise ValueError(f"Invalid recipient: {recipient}")

            message = self.format_message(recipient, **template_vars)
            metadata = {
                "priority": self.priority.name,
                "timestamp": self.timestamp.isoformat(),
            }
            return self.provider.send(message, recipient, metadata)
        except ValueError as e:
            print(f"Error sending notification: {e}")
            return False

    @abstractmethod
    def format_message(self, recipient: str) -> str:
        pass


# Concrete abstractions
class NormalNotification(Notification):
    def format_message(self, recipient: str, **template_vars) -> str:
        return self.template.format(recipient=recipient, **template_vars)


class UrgentNotification(Notification):
    def format_message(self, recipient: str, **template_vars) -> str:
        return f"URGENT: {self.template.format(recipient=recipient, **template_vars)}"


class MarketingNotification(Notification):
    def format_message(self, recipient: str, **template_vars) -> str:
        return f"*** {self.template.format(recipient=recipient, **template_vars)} ***"


# Priority queue for notifications
class NotificationQueue:
    def __init__(self):
        self.queue: List[Tuple[Notification, str]] = []
        self._counter = 0  # To maintain insertion order for same priority
        self.failed_notifications: List[Tuple[Notification, str]] = []

    def add_notification(
        self, notification: Notification, recipient: str, **template_vars
    ) -> None:
        heapq.heappush(
            self.queue,
            (
                -notification.priority.value,
                self._counter,
                (notification, recipient, template_vars),
            ),
        )
        self._counter += 1

    def process_notifications(self) -> Dict[str, int]:
        stats = {"sent": 0, "failed": 0, "total": 0}

        while self.queue:
            _, _, (notification, recipient, template_vars) = heapq.heappop(self.queue)
            stats["total"] += 1
            if notification.send(recipient, **template_vars):
                stats["sent"] += 1
            else:
                stats["failed"] += 1
                self.failed_notifications.append(
                    (notification, recipient, template_vars)
                )

        return stats

    def retry_failed(self) -> Dict[str, int]:
        stats = {"retried": 0, "failed": 0}
        to_retry = self.failed_notifications
        self.failed_notifications = []

        for notification, recipient, template_vars in to_retry:
            if notification.send(recipient, **template_vars):
                stats["retried"] += 1
            else:
                stats["failed"] += 1
                self.failed_notifications.append(
                    (notification, recipient, template_vars)
                )

        return stats


# Main function to test
def main():
    print("=== Bridge Pattern Notification System Demo ===\n")

    # Create providers
    email_provider = AWSSESProvider()
    sms_provider = TwilioSMSProvider()
    push_provider = PushNotificationProvider()

    # Create different types of notifications
    urgent_email = UrgentNotification(
        email_provider,
        "Hello {recipient}, your account shows suspicious activity at {time}!",
    )

    normal_sms = NormalNotification(
        sms_provider, "Hi {recipient}, your order #{order_id} has been shipped."
    )

    marketing_push = MarketingNotification(
        push_provider, "Hey {recipient}! Get {discount}% off your next purchase!"
    )

    # Create queue and add notifications
    queue = NotificationQueue()

    # Add notifications with template variables
    queue.add_notification(urgent_email, "john@example.com", time="2:30 PM")
    queue.add_notification(normal_sms, "+1234567890", order_id="12345")
    queue.add_notification(marketing_push, "user123", discount=25)

    # Process notifications
    stats = queue.process_notifications()
    print(f"\n📊 Processing complete: {stats['sent']} sent, {stats['failed']} failed")

    # Demonstrate flexibility: same notification type with different providers
    print("\n=== Demonstrating Bridge Flexibility ===")

    # Same urgent notification, different providers
    urgent_sms = UrgentNotification(
        sms_provider, "Critical alert for {recipient}: {alert}"
    )
    urgent_push = UrgentNotification(push_provider, "Emergency: {alert} - {recipient}")

    urgent_sms.send("+1987654321", alert="Server down")
    urgent_push.send("admin001", alert="Database connection lost")


if __name__ == "__main__":
    main()
