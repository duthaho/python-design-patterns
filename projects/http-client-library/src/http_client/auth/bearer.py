"""
Bearer token authentication strategy.

Pattern: Strategy (concrete implementation)

Bearer authentication adds an Authorization header:
    Authorization: Bearer <token>

Common use cases:
- API authentication with JWT tokens
- OAuth 2.0 access tokens
- Personal access tokens
"""

from ..models import Request
from .base import AuthStrategy


class BearerTokenAuth(AuthStrategy):
    """
    Bearer token authentication.

    Adds an "Authorization: Bearer <token>" header to requests.

    Example:
        auth = BearerTokenAuth("my_secret_token_123")
        auth.apply(request)
        # Request now has: Authorization: Bearer my_secret_token_123
    """

    def __init__(self, token: str):
        """
        Initialize bearer token authentication.

        Args:
            token: The bearer token to use for authentication

        Raises:
            ValueError: If token is empty or None
        """
        if not token or not token.strip():
            raise ValueError("Token must be a non-empty string")
        self.token = token.strip()

    def apply(self, request: Request) -> Request:
        """
        Apply bearer token authentication to the request.

        Adds "Authorization: Bearer <token>" header.

        Args:
            request: Request to authenticate

        Returns:
            Request with Authorization header added
        """
        request.headers["Authorization"] = f"Bearer {self.token}"
        return request

    def __repr__(self) -> str:
        """String representation (hide token for security)"""
        token_preview = self.token[:4] + "..." if len(self.token) > 4 else "***"
        return f"BearerTokenAuth(token={token_preview})"
