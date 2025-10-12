"""
API Key authentication strategy.

Pattern: Strategy (concrete implementation)

API Key authentication can be in:
1. Header: X-API-Key: <key>
2. Query parameter: ?api_key=<key>

Common use cases:
- REST API authentication
- Third-party service integration
- Public API access
"""

from typing import Literal

from ..models import Request
from .base import AuthStrategy


class APIKeyAuth(AuthStrategy):
    """
    API Key authentication.

    Adds API key to request header or query parameter.

    Examples:
        # API key in header
        auth = APIKeyAuth("secret123", location="header", param_name="X-API-Key")

        # API key in query param
        auth = APIKeyAuth("secret123", location="query", param_name="api_key")
    """

    def __init__(
        self,
        api_key: str,
        location: Literal["header", "query"] = "header",
        param_name: str = "X-API-Key",
    ):
        """
        Initialize API key authentication.

        Args:
            api_key: The API key to use
            location: Where to put the key ("header" or "query")
            param_name: Name of the header or query parameter

        Raises:
            ValueError: If api_key is empty or location is invalid
        """
        if not api_key or not api_key.strip():
            raise ValueError("API key must be a non-empty string")
        if location not in ("header", "query"):
            raise ValueError("Location must be 'header' or 'query'")
        self.api_key = api_key.strip()
        self.location = location
        self.param_name = param_name

    def apply(self, request: Request) -> Request:
        """
        Apply API key authentication to the request.

        Adds API key to header or query parameter based on location.

        Args:
            request: Request to authenticate

        Returns:
            Request with API key added
        """
        if self.location == "header":
            request.headers[self.param_name] = self.api_key
        elif self.location == "query":
            request.params[self.param_name] = self.api_key
        return request

    def __repr__(self) -> str:
        """String representation (hide key for security)"""
        key_preview = self.api_key[:4] + "..." if len(self.api_key) > 4 else "***"
        return f"APIKeyAuth(key={key_preview}, location={self.location}, param={self.param_name})"


def header_api_key(api_key: str, header_name: str = "X-API-Key") -> APIKeyAuth:
    """
    Create API key auth for header.

    Args:
        api_key: The API key
        header_name: Name of the header (default: X-API-Key)

    Returns:
        APIKeyAuth configured for header
    """
    return APIKeyAuth(api_key, location="header", param_name=header_name)


def query_api_key(api_key: str, param_name: str = "api_key") -> APIKeyAuth:
    """
    Create API key auth for query parameter.

    Args:
        api_key: The API key
        param_name: Name of the query param (default: api_key)

    Returns:
        APIKeyAuth configured for query parameter
    """
    return APIKeyAuth(api_key, location="query", param_name=param_name)
