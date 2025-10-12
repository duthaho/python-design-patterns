"""
Base class for authentication strategies.

Pattern: Strategy

Key concepts:
- Define common interface for all auth strategies
- Each strategy encapsulates a different authentication algorithm
- Strategies are interchangeable at runtime
"""

from abc import ABC, abstractmethod

from ..models import Request


class AuthStrategy(ABC):
    """
    Base class for all authentication strategies.

    The Strategy pattern allows us to define a family of authentication
    algorithms, encapsulate each one, and make them interchangeable.

    Example strategies:
    - Bearer token
    - Basic authentication
    - API key (header or query param)
    - OAuth2 (future)
    - JWT (future)
    """

    @abstractmethod
    def apply(self, request: Request) -> Request:
        """
        Apply authentication to the request.

        This method should modify the request to include authentication
        credentials (headers, query params, etc.).

        Args:
            request: The request to authenticate

        Returns:
            The request with authentication applied
        """
        pass

    def __repr__(self) -> str:
        """String representation for debugging"""
        return f"{self.__class__.__name__}()"
