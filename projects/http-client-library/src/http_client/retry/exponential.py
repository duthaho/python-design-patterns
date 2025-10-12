"""
Exponential backoff retry strategy.

Pattern: Strategy (concrete implementation)

Exponential backoff increases delay exponentially:
    delay = base_delay * (2 ** attempt)

Example with base_delay=1.0:
    Attempt 0: 1.0s
    Attempt 1: 2.0s
    Attempt 2: 4.0s
    Attempt 3: 8.0s
    Attempt 4: 16.0s

Benefits:
- Gives system time to recover
- Reduces server load during issues
- Industry standard approach
"""
from .base import RetryStrategy


class ExponentialBackoff(RetryStrategy):
    """
    Exponential backoff retry strategy.
    
    Delay doubles with each retry attempt, up to a maximum.
    
    Example:
        retry = ExponentialBackoff(
            max_retries=3,
            base_delay=1.0,
            max_delay=30.0
        )
        
        retry.calculate_delay(0)  # 1.0s
        retry.calculate_delay(1)  # 2.0s
        retry.calculate_delay(2)  # 4.0s
        retry.calculate_delay(3)  # 8.0s
    """
    
    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0
    ):
        """
        Initialize exponential backoff strategy.
        
        Args:
            max_retries: Maximum number of retry attempts
            base_delay: Base delay in seconds (first retry)
            max_delay: Maximum delay cap in seconds
            
        Raises:
            ValueError: If delays are invalid
        """
        super().__init__(max_retries)
        if base_delay <= 0:
            raise ValueError("base_delay must be positive")
        if max_delay < base_delay:
            raise ValueError("max_delay must be >= base_delay")
        self.base_delay = base_delay
        self.max_delay = max_delay
    
    def calculate_delay(self, attempt: int) -> float:
        """
        Calculate exponential delay.
        
        Formula: min(base_delay * (2 ** attempt), max_delay)
        
        Args:
            attempt: Current attempt number (0-indexed)
            
        Returns:
            Delay in seconds
            
        Example:
            With base_delay=1.0, max_delay=10.0:
            attempt 0: min(1.0 * 2^0, 10.0) = min(1.0, 10.0) = 1.0
            attempt 1: min(1.0 * 2^1, 10.0) = min(2.0, 10.0) = 2.0
            attempt 2: min(1.0 * 2^2, 10.0) = min(4.0, 10.0) = 4.0
            attempt 3: min(1.0 * 2^3, 10.0) = min(8.0, 10.0) = 8.0
            attempt 4: min(1.0 * 2^4, 10.0) = min(16.0, 10.0) = 10.0 (capped!)
        """
        delay = self.base_delay * (2 ** attempt)
        return min(delay, self.max_delay)
    
    def __repr__(self) -> str:
        """String representation for debugging"""
        return (
            f"ExponentialBackoff("
            f"max_retries={self.max_retries}, "
            f"base_delay={self.base_delay}, "
            f"max_delay={self.max_delay})"
        )
