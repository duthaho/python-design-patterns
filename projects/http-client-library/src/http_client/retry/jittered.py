"""
Jittered backoff retry strategy.

Pattern: Strategy (concrete implementation)

Jittered backoff adds randomness to exponential backoff:
    base_delay = base * (2 ** attempt)
    jitter = random value between 0 and (base_delay * jitter_factor)
    final_delay = base_delay + jitter

Example with base_delay=1.0, jitter_factor=0.3:
    Attempt 0: 1.0s + [0 to 0.3s] = 1.0-1.3s
    Attempt 1: 2.0s + [0 to 0.6s] = 2.0-2.6s
    Attempt 2: 4.0s + [0 to 1.2s] = 4.0-5.2s

Benefits:
- Prevents "thundering herd" problem
- Distributes retry load
- Better for distributed systems

Use case:
When many clients fail at same time (e.g., service restart),
jitter prevents all clients from retrying simultaneously.
"""

import random

from .base import RetryStrategy


class JitteredBackoff(RetryStrategy):
    """
    Exponential backoff with random jitter.

    Adds randomness to prevent synchronized retry storms.

    Example:
        retry = JitteredBackoff(
            max_retries=3,
            base_delay=1.0,
            max_delay=30.0,
            jitter_factor=0.3  # ±30% randomness
        )

        # Delays will vary randomly:
        retry.calculate_delay(0)  # 1.0s to 1.3s
        retry.calculate_delay(1)  # 2.0s to 2.6s
    """

    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        jitter_factor: float = 0.3,
    ):
        """
        Initialize jittered backoff strategy.

        Args:
            max_retries: Maximum number of retry attempts
            base_delay: Base delay in seconds
            max_delay: Maximum delay cap in seconds
            jitter_factor: Amount of jitter (0.0 to 1.0)
                          0.3 means ±30% randomness

        Raises:
            ValueError: If parameters are invalid
        """
        super().__init__(max_retries)
        if base_delay <= 0:
            raise ValueError("base_delay must be positive")
        if max_delay < base_delay:
            raise ValueError("max_delay must be >= base_delay")
        if not (0.0 <= jitter_factor <= 1.0):
            raise ValueError("jitter_factor must be between 0.0 and 1.0")
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.jitter_factor = jitter_factor

    def calculate_delay(self, attempt: int) -> float:
        """
        Calculate delay with jitter.

        Formula:
            base = base_delay * (2 ** attempt)
            jitter = random.uniform(0, base * jitter_factor)
            delay = min(base + jitter, max_delay)

        Args:
            attempt: Current attempt number (0-indexed)

        Returns:
            Delay in seconds (with random jitter)

        Example:
            With base_delay=1.0, jitter_factor=0.3:
            attempt 0: 1.0 * 2^0 + [0 to 0.3] = 1.0 to 1.3s
            attempt 1: 1.0 * 2^1 + [0 to 0.6] = 2.0 to 2.6s
            attempt 2: 1.0 * 2^2 + [0 to 1.2] = 4.0 to 5.2s
        """
        base = self.base_delay * (2**attempt)
        jitter = random.uniform(0, base * self.jitter_factor)
        return min(base + jitter, self.max_delay)

    def __repr__(self) -> str:
        """String representation for debugging"""
        return (
            f"JitteredBackoff("
            f"max_retries={self.max_retries}, "
            f"base_delay={self.base_delay}, "
            f"max_delay={self.max_delay}, "
            f"jitter_factor={self.jitter_factor})"
        )


class FullJitterBackoff(RetryStrategy):
    """
    Full jitter backoff (AWS best practice).

    Instead of adding jitter to exponential delay,
    picks a random value between 0 and exponential delay.

    Formula: random.uniform(0, min(base_delay * (2 ** attempt), max_delay))

    This provides even better distribution than additive jitter.
    """

    def __init__(self, max_retries: int = 3, base_delay: float = 1.0, max_delay: float = 60.0):
        super().__init__(max_retries)
        self.base_delay = base_delay
        self.max_delay = max_delay

    def calculate_delay(self, attempt: int) -> float:
        """Calculate full jitter delay"""
        cap = min(self.base_delay * (2**attempt), self.max_delay)
        return random.uniform(0, cap)
