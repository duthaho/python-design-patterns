"""
Base class for retry strategies.

Pattern: Strategy

Key concepts:
- Define common interface for retry algorithms
- Each strategy calculates delays differently
- Strategies determine which errors are retryable
"""

from abc import ABC, abstractmethod

import requests


class RetryStrategy(ABC):
    """
    Base class for all retry strategies.

    Retry strategies control:
    1. How many times to retry
    2. How long to wait between retries
    3. Which errors should trigger a retry
    """

    def __init__(self, max_retries: int = 3):
        """
        Initialize retry strategy.

        Args:
            max_retries: Maximum number of retry attempts

        Raises:
            ValueError: If max_retries is negative
        """
        if max_retries < 0:
            raise ValueError("max_retries must be non-negative")
        self.max_retries = max_retries

    @abstractmethod
    def calculate_delay(self, attempt: int) -> float:
        """
        Calculate delay before next retry attempt.

        Args:
            attempt: Current attempt number (0-indexed)
                    0 = first retry, 1 = second retry, etc.

        Returns:
            Delay in seconds before next retry

        Example:
            strategy = ExponentialBackoff(base_delay=1.0)
            strategy.calculate_delay(0)  # Returns 1.0
            strategy.calculate_delay(1)  # Returns 2.0
            strategy.calculate_delay(2)  # Returns 4.0
        """
        pass

    def should_retry(self, attempt: int, exception: Exception) -> bool:
        """
        Determine if request should be retried.

        Args:
            attempt: Current attempt number (0-indexed)
            exception: Exception that occurred

        Returns:
            True if should retry, False otherwise
        """
        if attempt >= self.max_retries:
            return False
        if not self.is_retryable_error(exception):
            return False
        return True

    def is_retryable_error(self, exception: Exception) -> bool:
        """
        Determine if an error is retryable.

        Retryable errors:
        - Network errors (ConnectionError, Timeout)
        - Server errors (5xx status codes)
        - Rate limiting (429 status code)

        Non-retryable errors:
        - Client errors (4xx except 429)
        - Successful responses (2xx, 3xx)

        Args:
            exception: Exception to check

        Returns:
            True if error should be retried
        """
        if isinstance(
            exception, (requests.exceptions.ConnectionError, requests.exceptions.Timeout)
        ):
            return True
        if isinstance(exception, requests.exceptions.HTTPError):
            status_code = get_status_code(exception)
            if status_code == 429 or (500 <= status_code < 600):
                return True
            return False
        return False

    def __repr__(self) -> str:
        """String representation for debugging"""
        return f"{self.__class__.__name__}(max_retries={self.max_retries})"


def get_status_code(exception: Exception) -> int:
    """
    Extract HTTP status code from exception if available.

    Args:
        exception: Exception to extract status from

    Returns:
        Status code or 0 if not available
    """
    if hasattr(exception, "response") and hasattr(exception.response, "status_code"):
        return exception.response.status_code
    return 0
