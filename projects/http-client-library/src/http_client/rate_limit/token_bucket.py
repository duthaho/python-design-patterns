"""
Token bucket rate limiting algorithm.

Pattern: State

Token bucket algorithm:
- Bucket holds tokens (capacity)
- Tokens are added at a constant rate
- Each request consumes 1 token
- If no tokens available, request is blocked/delayed

Use cases:
- API rate limiting
- Prevent overload
- Smooth traffic bursts
"""

import time
from threading import RLock


class TokenBucket:
    """
    Token bucket rate limiter.

    Algorithm:
    1. Bucket starts full (capacity tokens)
    2. Tokens refill at rate per second
    3. Each request tries to acquire 1 token
    4. If tokens available: request proceeds
    5. If no tokens: request blocked/delayed

    Example:
        # 10 requests per second, burst of 20
        bucket = TokenBucket(rate=10, capacity=20)

        if bucket.acquire():
            make_request()
        else:
            print("Rate limited!")
    """

    def __init__(self, rate: float, capacity: int):
        """
        Initialize token bucket.

        Args:
            rate: Tokens added per second
            capacity: Maximum tokens in bucket

        Raises:
            ValueError: If rate or capacity invalid
        """
        if rate <= 0:
            raise ValueError("rate must be positive")
        if capacity <= 0:
            raise ValueError("capacity must be positive")

        self.rate = rate
        self.capacity = capacity
        self.tokens = capacity  # Start full
        self.last_update = time.time()
        self._lock = RLock()

    def acquire(self, tokens: int = 1, blocking: bool = True, timeout: float = None) -> bool:
        """
        Try to acquire tokens.

        Args:
            tokens: Number of tokens to acquire
            blocking: If True, wait until tokens available
            timeout: Maximum time to wait (seconds)

        Returns:
            True if tokens acquired, False if not available
        """
        with self._lock:
            self._refill()
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            elif not blocking:
                return False
            else:
                start_time = time.time()
                while True:
                    wait_time = (tokens - self.tokens) / self.rate
                    if timeout is not None and (time.time() - start_time + wait_time) > timeout:
                        return False
                    time.sleep(wait_time)
                    self._refill()
                    if self.tokens >= tokens:
                        self.tokens -= tokens
                        return True

    def _refill(self) -> None:
        """
        Refill tokens based on elapsed time.
        """
        now = time.time()
        elapsed = now - self.last_update
        new_tokens = self.tokens + (elapsed * self.rate)
        self.tokens = min(new_tokens, self.capacity)
        self.last_update = now

    def available_tokens(self) -> float:
        """
        Get number of available tokens.

        Returns:
            Number of tokens currently available
        """
        with self._lock:
            self._refill()
            return self.tokens

    def wait_time(self, tokens: int = 1) -> float:
        """
        Calculate time to wait for tokens.

        Args:
            tokens: Number of tokens needed

        Returns:
            Time to wait in seconds
        """
        with self._lock:
            self._refill()
            if self.tokens >= tokens:
                return 0.0
            deficit = tokens - self.tokens
            return deficit / self.rate

    def reset(self) -> None:
        """Reset bucket to full capacity"""
        with self._lock:
            self.tokens = self.capacity
            self.last_update = time.time()

    def __repr__(self) -> str:
        return f"TokenBucket(rate={self.rate}, capacity={self.capacity}, tokens={self.tokens:.2f})"


class DistributedTokenBucket(TokenBucket):
    def __init__(self, redis_client, key, rate, capacity):
        # Store tokens in Redis for multi-process rate limiting
        pass
