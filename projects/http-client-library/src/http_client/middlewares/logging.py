"""
Logging middleware for request/response logging.

Pattern: Chain of Responsibility (concrete implementation)

This is a simple example middleware showing how to:
- Implement the Middleware interface
- Log request details before sending
- Log response details after receiving
"""

import logging
from typing import Dict

from ..middleware import Middleware
from ..models import Request, Response

logger = logging.getLogger(__name__)


class LoggingMiddleware(Middleware):
    """
    Logs all HTTP requests and responses.

    Useful for debugging and monitoring.
    """

    def __init__(self, log_level: int = logging.INFO):
        """
        Initialize logging middleware.

        Args:
            log_level: Python logging level (INFO, DEBUG, etc.)
        """
        super().__init__()
        self.log_level = log_level

    def process_request(self, request: Request) -> Request:
        """
        Log outgoing request details.

        Args:
            request: Request to log

        Returns:
            Unmodified request
        """
        logger.log(self.log_level, f"→ {request.method} {request.url}")
        return request

    def process_response(self, response: Response) -> Response:
        """
        Log incoming response details.

        Args:
            response: Response to log

        Returns:
            Unmodified response
        """
        logger.log(
            self.log_level,
            f"← {response.status_code} {response.url} ({response.elapsed_ms:.2f}ms)",
        )
        return response


class HeaderMiddleware(Middleware):
    """Adds custom headers to all requests"""

    def __init__(self, headers: Dict[str, str]):
        super().__init__()
        self.headers = headers

    def process_request(self, request: Request) -> Request:
        """
        Add custom headers to the request.

        Args:
            request: Request to modify

        Returns:
            Modified request with added headers
        """
        request.headers.update(self.headers)
        return request

    def process_response(self, response: Response) -> Response:
        """No-op for response"""
        return response
