"""
Custom exceptions for the notification system.
Pattern: Exception Hierarchy for different error types
"""


class NotificationError(Exception):
    """Base exception for all notification errors"""

    pass


class ValidationError(NotificationError):
    """Raised when notification validation fails"""

    pass


class ChannelError(NotificationError):
    """Base exception for channel-specific errors"""

    def __init__(self, message: str, channel: str, retriable: bool = False):
        super().__init__(message)
        self.channel = channel
        self.retriable = retriable


class RetriableError(ChannelError):
    """Error that should trigger a retry"""

    def __init__(self, message: str, channel: str):
        super().__init__(message, channel, retriable=True)


class PermanentError(ChannelError):
    """Error that should NOT trigger a retry"""

    def __init__(self, message: str, channel: str):
        super().__init__(message, channel, retriable=False)


class ConnectionError(RetriableError):
    """Connection to provider failed"""

    pass


class TimeoutError(RetriableError):
    """Request timed out"""

    pass


class AuthenticationError(PermanentError):
    """Authentication with provider failed"""

    pass


class InvalidRecipientError(PermanentError):
    """Recipient address is invalid"""

    pass
