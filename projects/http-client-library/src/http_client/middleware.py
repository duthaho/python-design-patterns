"""
Base middleware classes implementing Chain of Responsibility pattern.

Pattern: Chain of Responsibility

Key concepts:
- Each middleware can process request/response
- Middlewares are chained together
- Request flows forward through chain
- Response flows backward through chain (reverse order)
"""

from abc import ABC, abstractmethod
from typing import Optional

from .models import Request, Response


class Middleware(ABC):
    """
    Base class for all middleware (stateless).

    Each middleware:
    1. Processes the request/response
    2. Passes it to the next middleware in chain

    Important: Middleware should be STATELESS.
    Any state should be managed by external managers (Phase 3+).
    """

    def __init__(self):
        self.next_middleware: Optional["Middleware"] = None

    def set_next(self, middleware: "Middleware") -> "Middleware":
        """
        Set the next middleware in chain.

        Args:
            middleware: The next middleware to call

        Returns:
            The middleware that was set (for chaining)
        """
        self.next_middleware = middleware
        return middleware

    def handle_request(self, request: Request) -> Request:
        """Handle request through the chain."""
        request = self.process_request(request)
        if self.next_middleware:
            return self.next_middleware.handle_request(request)
        return request

    def handle_response(self, response: Response) -> Response:
        """
        Handle response through the chain (in REVERSE order).

        Flow:
        1. Pass to next middleware first (if exists)
        2. Then process in current middleware
        3. Return processed response

        Why reverse? Response processing happens after HTTP call,
        so we unwind the chain: last middleware processes first.
        """
        if self.next_middleware:
            response = self.next_middleware.handle_response(response)
        return self.process_response(response)

    @abstractmethod
    def process_request(self, request: Request) -> Request:
        """
        Process/modify the request.

        Override this in concrete middleware to:
        - Add headers
        - Modify URL/params
        - Log request
        - Check authentication
        - etc.

        Args:
            request: The request to process

        Returns:
            Modified request (can return same object)
        """
        pass

    @abstractmethod
    def process_response(self, response: Response) -> Response:
        """
        Process/modify the response.

        Override this in concrete middleware to:
        - Parse response
        - Log response
        - Cache response
        - Handle errors
        - etc.

        Args:
            response: The response to process

        Returns:
            Modified response (can return same object)
        """
        pass


class MiddlewarePipeline:
    """
    Manages the middleware chain.

    Responsibilities:
    - Maintain ordered list of middleware
    - Execute request through chain
    - Execute response through chain (reverse)
    """

    def __init__(self):
        self.head: Optional[Middleware] = None
        self.tail: Optional[Middleware] = None

    def add(self, middleware: Middleware) -> "MiddlewarePipeline":
        """
        Add middleware to the end of chain.

        Args:
            middleware: Middleware to add

        Returns:
            Self for method chaining

        TODO: Implement chain building logic
        Implementation tips:
        - If no head, set both head and tail to middleware
        - Otherwise, link tail to new middleware and update tail
        - Return self for fluent API
        """
        if self.head is None:
            self.head = middleware
            self.tail = middleware
        else:
            self.tail.set_next(middleware)
            self.tail = middleware
        return self

    def execute_request(self, request: Request) -> Request:
        """
        Execute request through all middleware.

        Args:
            request: The request to process

        Returns:
            Processed request after going through all middleware
        """
        if self.head:
            return self.head.handle_request(request)
        return request

    def execute_response(self, response: Response) -> Response:
        """
        Execute response through all middleware (reverse order).

        Args:
            response: The response to process

        Returns:
            Processed response after going through all middleware
        """
        if self.head:
            return self.head.handle_response(response)
        return response
