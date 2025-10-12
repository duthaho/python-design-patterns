"""
HTTP Client with Builder pattern.

Pattern: Builder

Key concepts:
- HTTPClient: Main client class (wraps requests.Session)
- HTTPClientBuilder: Fluent API for configuration
- Separation of construction from representation
"""
from typing import Any, Dict, Optional

import requests

from .exceptions import RequestError, TimeoutError
from .middleware import Middleware, MiddlewarePipeline
from .models import Request, Response


class HTTPClient:
    """
    Main HTTP client with middleware support.
    
    Uses requests.Session internally for connection pooling.
    Supports middleware pipeline for request/response processing.
    """
    
    def __init__(self, base_url: str = "", timeout: float = 30.0):
        """
        Initialize HTTP client.
        
        Args:
            base_url: Base URL for all requests (optional)
            timeout: Default timeout in seconds
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.session = requests.Session()
        self.pipeline = MiddlewarePipeline()
    
    def _make_request(self, request: Request) -> Response:
        """Internal method to execute HTTP request through middleware pipeline."""
        try:
            processed_request = self.pipeline.execute_request(request)

            req_kwargs = processed_request.to_requests_kwargs()
            req_kwargs.setdefault("timeout", self.timeout)

            raw_response = self.session.request(**req_kwargs)
            response = Response.from_requests_response(raw_response)

            processed_response = self.pipeline.execute_response(response)
            return processed_response
        except requests.exceptions.Timeout as e:
            raise TimeoutError(f"Request timed out: {e}")
        except requests.exceptions.RequestException as e:
            raise RequestError(f"Request failed: {e}")
    
    def get(self, path: str, params: Optional[Dict] = None, **kwargs) -> Response:
        """HTTP GET request."""
        url = f"{self.base_url}/{path.lstrip('/')}" if self.base_url else path
        request = Request(method="GET", url=url, params=params or {}, **kwargs)
        return self._make_request(request)
    
    def post(
        self, 
        path: str, 
        json: Optional[Dict] = None, 
        data: Optional[Any] = None, 
        **kwargs
    ) -> Response:
        """HTTP POST request."""
        url = f"{self.base_url}/{path.lstrip('/')}" if self.base_url else path
        request = Request(method="POST", url=url, json=json, data=data, **kwargs)
        return self._make_request(request)
    
    def put(self, path: str, json: Optional[Dict] = None, **kwargs) -> Response:
        """HTTP PUT request."""
        url = f"{self.base_url}/{path.lstrip('/')}" if self.base_url else path
        request = Request(method="PUT", url=url, json=json, **kwargs)
        return self._make_request(request)
    
    def delete(self, path: str, **kwargs) -> Response:
        """HTTP DELETE request."""
        url = f"{self.base_url}/{path.lstrip('/')}" if self.base_url else path
        request = Request(method="DELETE", url=url, **kwargs)
        return self._make_request(request)
    
    def close(self):
        """Close the underlying session."""
        self.session.close()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
    
    @staticmethod
    def builder() -> 'HTTPClientBuilder':
        """
        Create a new builder instance.
        
        Returns:
            HTTPClientBuilder for fluent configuration
        """
        return HTTPClientBuilder()


class HTTPClientBuilder:
    """
    Builder pattern for HTTPClient configuration.
    
    Provides fluent API for constructing configured client:
    
    client = HTTPClient.builder() \
        .base_url("https://api.example.com") \
        .timeout(10.0) \
        .add_middleware(LoggingMiddleware()) \
        .build()
    """
    
    def __init__(self):
        """Initialize builder with default values."""
        self._base_url: str = ""
        self._timeout: float = 30.0
        self._middlewares: list[Middleware] = []
    
    def base_url(self, url: str) -> 'HTTPClientBuilder':
        """
        Set base URL for all requests.
        
        Args:
            url: Base URL (e.g., "https://api.example.com")
            
        Returns:
            Self for method chaining
        """
        self._base_url = url.rstrip('/')
        return self
    
    def timeout(self, seconds: float) -> 'HTTPClientBuilder':
        """
        Set default timeout for requests.
        
        Args:
            seconds: Timeout in seconds
            
        Returns:
            Self for method chaining
        """
        self._timeout = seconds
        return self
    
    def add_middleware(self, middleware: Middleware) -> 'HTTPClientBuilder':
        """
        Add middleware to the pipeline.
        
        Middlewares are executed in the order they are added.
        
        Args:
            middleware: Middleware instance to add
            
        Returns:
            Self for method chaining
        """
        self._middlewares.append(middleware)
        return self
    
    def build(self) -> HTTPClient:
        """
        Build the configured HTTPClient.
        
        Returns:
            Configured HTTPClient instance
        """
        client = HTTPClient(base_url=self._base_url, timeout=self._timeout)
        for middleware in self._middlewares:
            client.pipeline.add(middleware)
        return client
