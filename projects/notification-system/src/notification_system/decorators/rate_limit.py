"""
Rate limiting decorator using token bucket algorithm.
Pattern: Decorator Pattern (adds rate limiting)
"""

import threading
import time
from typing import Any

from ..channels.base import ChannelProtocol
from ..core.notification import Notification, NotificationResult


class RateLimitDecorator:
    """
    Adds rate limiting to prevent exceeding provider limits.

    Uses Token Bucket algorithm with thread-safe implementation.
    """

    def __init__(
        self,
        wrapped: ChannelProtocol,
        rate_limit: int = 10,
        time_window: float = 60.0,
        max_wait: float = 30.0,
    ):
        """Initialize rate limiter."""
        self.wrapped = wrapped
        self.rate_limit = float(rate_limit)
        self.time_window = time_window
        self.max_wait = max_wait
        self.tokens = float(rate_limit)  # Start with full bucket
        self.last_refill = time.time()
        self.lock = threading.Lock()
        self.refill_rate = self.rate_limit / time_window  # tokens per second

    def send(self, notification: Notification) -> NotificationResult:
        """Send with rate limiting."""
        if self._acquire_token():
            return self.wrapped.send(notification)
        else:
            error_message = (
                f"Rate limit exceeded for {notification.channel}. "
                f"Notification {notification.notification_id} not sent."
            )
            return NotificationResult(
                success=False,
                channel=notification.channel,
                message=error_message,
                sent_at=None,
                metadata={
                    "rate_limit": self.rate_limit,
                    "time_window": self.time_window,
                },
            )

    def _acquire_token(self) -> bool:
        """Try to acquire a token from the bucket."""
        with self.lock:
            self._refill_tokens()
            
            if self.tokens >= 1:
                self.tokens -= 1
                return True
            
            # Calculate wait time
            wait_time = (1.0 - self.tokens) / self.refill_rate
            
            if wait_time > self.max_wait:
                return False
            
            # If we need to wait, check if it's worth waiting
            # For simplicity, just return False if no tokens available
            # This is more conservative but thread-safe
            return False

    def _refill_tokens(self) -> None:
        """Refill tokens based on elapsed time since last refill."""
        now = time.time()
        elapsed = now - self.last_refill

        if elapsed > 0:
            # Calculate tokens to add
            refill_amount = elapsed * self.refill_rate

            # Add tokens, capped at rate_limit
            self.tokens = min(self.rate_limit, self.tokens + refill_amount)

            # Update last refill time
            self.last_refill = now

    def __getattr__(self, name: str) -> Any:
        """Delegate attribute access to wrapped object."""
        return getattr(self.wrapped, name)

    def __repr__(self) -> str:
        return (
            f"RateLimitDecorator(wrapped={self.wrapped}, "
            f"rate_limit={self.rate_limit}, time_window={self.time_window})"
        )
