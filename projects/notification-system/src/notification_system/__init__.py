"""
Notification System - A production-ready notification framework.

Usage:
    from notification_system import NotificationManager

    # Initialize from config
    manager = NotificationManager.from_config()

    # Send event-based notifications
    manager.send_event(
        'user.signup',
        username='john',
        email='john@example.com'
    )

    # Send direct notifications
    manager.send_notification(
        channel='email',
        recipients=['user@example.com'],
        subject='Hello',
        body='Welcome!'
    )
"""

__version__ = "1.0.0"

from .core.event import Event, EventPriority
from .core.notification import (Notification, NotificationResult,
                                NotificationStatus)
from .factories import ChannelFactory, DecoratorFactory
from .manager import NotificationManager

__all__ = [
    "NotificationManager",
    "Event",
    "EventPriority",
    "Notification",
    "NotificationResult",
    "NotificationStatus",
    "ChannelFactory",
    "DecoratorFactory",
]
