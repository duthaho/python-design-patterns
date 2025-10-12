"""
Authentication middleware.

Pattern: Strategy (used by middleware) + Dependency Injection

This middleware delegates authentication to a pluggable AuthStrategy.
This is a great example of:
- Strategy pattern: Different auth algorithms
- Dependency Injection: Strategy injected into middleware
- Open/Closed Principle: Open for extension (new strategies), closed for modification
"""

from ..auth.base import AuthStrategy
from ..middleware import Middleware
from ..models import Request, Response


class AuthMiddleware(Middleware):
    """
    Middleware that applies authentication using a strategy.
    
    This middleware doesn't know HOW to authenticate - it delegates
    to the injected AuthStrategy. This makes it flexible and testable.
    
    Example:
        from http_client.auth.bearer import BearerTokenAuth
        
        auth_strategy = BearerTokenAuth("secret_token")
        auth_middleware = AuthMiddleware(auth_strategy)
        
        client = HTTPClient.builder() \\
            .add_middleware(auth_middleware) \\
            .build()
    """

    def __init__(self, auth_strategy: AuthStrategy):
        """
        Initialize authentication middleware.

        Args:
            auth_strategy: The authentication strategy to use

        Raises:
            TypeError: If auth_strategy is not an AuthStrategy
        """
        super().__init__()
        if not isinstance(auth_strategy, AuthStrategy):
            raise TypeError("auth_strategy must be an instance of AuthStrategy")
        self.auth_strategy = auth_strategy

    def process_request(self, request: Request) -> Request:
        """
        Apply authentication to the request.

        Delegates to the auth strategy's apply() method.

        Args:
            request: Request to authenticate

        Returns:
            Request with authentication applied
        """
        return self.auth_strategy.apply(request)

    def process_response(self, response: Response) -> Response:
        """
        No-op for response.

        Authentication is only needed for requests, not responses.
        (Though you might want to handle 401 Unauthorized in the future)

        Args:
            response: Response to process

        Returns:
            Unmodified response
        """
        return response  # No-op

    def __repr__(self) -> str:
        """String representation for debugging"""
        return f"AuthMiddleware(strategy={self.auth_strategy})"
