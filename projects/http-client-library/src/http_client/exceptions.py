"""
Custom exceptions for HTTP client library.
"""

__all__ = [
    "HTTPClientError",
    "RequestError",
    "ResponseError",
    "TimeoutError",
    "MiddlewareError",
    "RetryExhaustedError",
    "AuthenticationError",
]


class HTTPClientError(Exception):
    """Base exception for all HTTP client errors"""

    pass


class RequestError(HTTPClientError):
    """Raised when request fails before reaching server"""

    pass


class ResponseError(HTTPClientError):
    """Raised when response indicates an error"""

    def __init__(self, message: str, status_code: int, response=None):
        super().__init__(message)
        self.status_code = status_code
        self.response = response


class TimeoutError(RequestError):
    """Raised when request times out"""

    pass


class MiddlewareError(HTTPClientError):
    """Raised when middleware processing fails"""

    pass


class RetryExhaustedError(RequestError):
    """Raised when all retry attempts are exhausted"""

    def __init__(self, message: str, attempts: int, last_exception: Exception):
        """
        Initialize retry exhausted error.

        Args:
            message: Error message
            attempts: Number of attempts made
            last_exception: The last exception that occurred
        """
        super().__init__(message)
        self.attempts = attempts
        self.last_exception = last_exception

    def __str__(self) -> str:
        return (
            f"{self.args[0]} "
            f"(after {self.attempts} attempts, "
            f"last error: {self.last_exception})"
        )


class AuthenticationError(ResponseError):
    """Raised when authentication fails (401 Unauthorized)"""

    def __init__(self, message: str = "Authentication failed", response=None):
        super().__init__(message, status_code=401, response=response)
