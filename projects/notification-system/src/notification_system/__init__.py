"""
Notification System - A production-ready notification framework.
"""

__version__ = "0.1.0"

from .core.event import Event, EventPriority
from .core.exceptions import (ChannelError, NotificationError, PermanentError,
                              RetriableError, ValidationError)
from .core.notification import (Notification, NotificationResult,
                                NotificationStatus)

__all__ = [
    "Event",
    "EventPriority",
    "Notification",
    "NotificationResult",
    "NotificationStatus",
    "NotificationError",
    "ValidationError",
    "ChannelError",
    "RetriableError",
    "PermanentError",
]
