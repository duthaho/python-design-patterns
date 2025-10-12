"""
Rate limiting middleware.

Pattern: State

Uses token bucket algorithm to enforce rate limits on requests.
"""

import logging
from typing import Dict

from ..middleware import Middleware
from ..models import Request, Response
from ..rate_limit.token_bucket import TokenBucket

logger = logging.getLogger(__name__)


class RateLimitMiddleware(Middleware):
    """
    Middleware that enforces rate limits.
    
    Uses token bucket algorithm to limit request rate.
    Can have per-endpoint limits or global limits.
    
    Example:
        # Global rate limit: 10 requests per second
        rate_limit = RateLimitMiddleware(rate=10, capacity=20)
        
        client = HTTPClient.builder() \\
            .add_middleware(rate_limit) \\
            .build()
    """

    def __init__(self, rate: float, capacity: int, per_endpoint: bool = False):
        """
        Initialize rate limit middleware.

        Args:
            rate: Requests per second
            capacity: Burst capacity (max tokens)
            per_endpoint: If True, rate limit per endpoint
        """
        super().__init__()
        self.rate = rate
        self.capacity = capacity
        self.per_endpoint = per_endpoint
        if per_endpoint:
            self._buckets: Dict[str, TokenBucket] = {}

    def process_request(self, request: Request) -> Request:
        """
        Check rate limit before request.

        Args:
            request: Request to check

        Returns:
            Request (possibly delayed)
        """
        bucket = self._get_bucket(self._get_endpoint(request) if self.per_endpoint else None)
        if not bucket.acquire(blocking=True):
            logger.warning(f"Request to {request.url} was rate limited.")
        return request

    def process_response(self, response: Response) -> Response:
        """No-op for response"""
        return response

    def _get_bucket(self, endpoint: str = None) -> TokenBucket:
        """
        Get token bucket for endpoint or global.

        Args:
            endpoint: Endpoint URL (if per_endpoint=True)

        Returns:
            TokenBucket instance
        """
        if not self.per_endpoint:
            if not hasattr(self, "_global_bucket"):
                self._global_bucket = TokenBucket(rate=self.rate, capacity=self.capacity)
            return self._global_bucket
        else:
            if endpoint not in self._buckets:
                self._buckets[endpoint] = TokenBucket(rate=self.rate, capacity=self.capacity)
            return self._buckets[endpoint]

    def _get_endpoint(self, request: Request) -> str:
        """Extract endpoint from request"""
        # Use URL without query params as endpoint
        return request.url.split("?")[0]

    def reset(self) -> None:
        """Reset all rate limiters"""
        if self.per_endpoint:
            for bucket in self._buckets.values():
                bucket.reset()
        else:
            self._global_bucket.reset()

    def __repr__(self) -> str:
        return f"RateLimitMiddleware(rate={self.rate}, capacity={self.capacity})"
