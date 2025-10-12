"""
HTTP Client Library - A production-ready HTTP client with middleware support.

Usage:
    from http_client import HTTPClient
    from http_client.middlewares.logging import LoggingMiddleware
    
    client = HTTPClient.builder() \\
        .base_url("https://api.example.com") \\
        .add_middleware(LoggingMiddleware()) \\
        .build()
    
    response = client.get("/endpoint")
"""

from .client import HTTPClient, HTTPClientBuilder
from .exceptions import HTTPClientError, MiddlewareError, RequestError, ResponseError, TimeoutError
from .middleware import Middleware, MiddlewarePipeline
from .models import Request, Response

__version__ = "0.1.0"
__all__ = [
    "HTTPClient",
    "HTTPClientBuilder",
    "Request",
    "Response",
    "Middleware",
    "MiddlewarePipeline",
    "HTTPClientError",
    "RequestError",
    "ResponseError",
    "TimeoutError",
    "MiddlewareError",
]
