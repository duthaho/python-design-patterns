"""
Basic authentication strategy.

Pattern: Strategy (concrete implementation)

Basic authentication encodes username:password in base64:
    Authorization: Basic <base64(username:password)>

Common use cases:
- Simple API authentication
- Internal service authentication
- Legacy system integration
"""

import base64

from ..models import Request
from .base import AuthStrategy


class BasicAuth(AuthStrategy):
    """
    HTTP Basic authentication.

    Encodes username and password in base64 and adds to Authorization header.

    Example:
        auth = BasicAuth("john", "secret123")
        auth.apply(request)
        # Request now has: Authorization: Basic am9objpzZWNyZXQxMjM=
    """

    def __init__(self, username: str, password: str):
        """
        Initialize basic authentication.

        Args:
            username: Username for authentication
            password: Password for authentication

        Raises:
            ValueError: If username is empty
        """
        if not username:
            raise ValueError("username cannot be empty")
        
        self.username = username
        self.password = password

    def apply(self, request: Request) -> Request:
        """
        Apply basic authentication to the request.

        Encodes credentials as base64 and adds Authorization header.

        Args:
            request: Request to authenticate

        Returns:
            Request with Authorization header added
        """
        auth = encode_basic_auth(self.username, self.password)
        request.headers["Authorization"] = f"Basic {auth}"
        return request

    def __repr__(self) -> str:
        """String representation (hide password for security)"""
        return f"BasicAuth(username={self.username}, password=***)"


def encode_basic_auth(username: str, password: str) -> str:
    """
    Encode username and password for basic auth.

    Args:
        username: Username
        password: Password

    Returns:
        Base64 encoded credentials string

    Example:
        >>> encode_basic_auth("user", "pass")
        'dXNlcjpwYXNz'
    """
    credentials = f"{username}:{password}"
    encoded = base64.b64encode(credentials.encode("utf-8")).decode("utf-8")
    return encoded
