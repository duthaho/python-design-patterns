"""
Custom exceptions for HTTP client library.
"""


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
