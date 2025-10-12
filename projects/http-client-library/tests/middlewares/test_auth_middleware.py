"""
Tests for authentication middleware.

Pattern: Strategy + Dependency Injection (testing)
"""

from datetime import timedelta
from unittest.mock import Mock

import pytest

from http_client.auth.api_key import APIKeyAuth
from http_client.auth.base import AuthStrategy
from http_client.auth.basic import BasicAuth
from http_client.auth.bearer import BearerTokenAuth
from http_client.middlewares.auth import AuthMiddleware
from http_client.models import Request, Response


# Test implementation of AuthStrategy for testing delegation
class MockAuthStrategy(AuthStrategy):
    """Mock auth strategy for testing delegation"""

    def __init__(self):
        self.apply_called = False
        self.apply_called_with = None

    def apply(self, request: Request) -> Request:
        self.apply_called = True
        self.apply_called_with = request
        # Mark that this strategy was applied
        request.headers["X-Mock-Auth"] = "applied"
        return request


class TestAuthMiddleware:
    """Test AuthMiddleware"""

    def test_initialization(self):
        """Test middleware initializes with auth strategy"""
        auth_strategy = BearerTokenAuth("token")
        middleware = AuthMiddleware(auth_strategy)

        assert middleware.auth_strategy == auth_strategy

    def test_initialization_with_invalid_strategy_raises_error(self):
        """Test that non-AuthStrategy raises TypeError"""
        with pytest.raises(TypeError, match="must be an instance of AuthStrategy"):
            AuthMiddleware("not_a_strategy")

    def test_process_request_delegates_to_strategy(self):
        """Test that process_request calls auth_strategy.apply()"""
        # Use our test implementation instead of Mock
        auth_strategy = MockAuthStrategy()
        middleware = AuthMiddleware(auth_strategy)
        request = Request(method="GET", url="http://test.com")

        result = middleware.process_request(request)

        # Verify strategy.apply() was called
        assert auth_strategy.apply_called is True
        assert auth_strategy.apply_called_with == request
        assert result.headers["X-Mock-Auth"] == "applied"

    def test_process_request_with_bearer_auth(self):
        """Test process_request with BearerTokenAuth"""
        auth_strategy = BearerTokenAuth("test_token")
        middleware = AuthMiddleware(auth_strategy)
        request = Request(method="GET", url="http://test.com")

        result = middleware.process_request(request)

        assert result.headers["Authorization"] == "Bearer test_token"

    def test_process_request_with_basic_auth(self):
        """Test process_request with BasicAuth"""
        auth_strategy = BasicAuth("user", "pass")
        middleware = AuthMiddleware(auth_strategy)
        request = Request(method="GET", url="http://test.com")

        result = middleware.process_request(request)

        assert "Authorization" in result.headers
        assert result.headers["Authorization"].startswith("Basic ")

    def test_process_request_with_api_key_header(self):
        """Test process_request with APIKeyAuth in header"""
        auth_strategy = APIKeyAuth("key123", location="header", param_name="X-API-Key")
        middleware = AuthMiddleware(auth_strategy)
        request = Request(method="GET", url="http://test.com")

        result = middleware.process_request(request)

        assert result.headers["X-API-Key"] == "key123"

    def test_process_request_with_api_key_query(self):
        """Test process_request with APIKeyAuth in query"""
        auth_strategy = APIKeyAuth("key123", location="query", param_name="api_key")
        middleware = AuthMiddleware(auth_strategy)
        request = Request(method="GET", url="http://test.com")

        result = middleware.process_request(request)

        assert result.params["api_key"] == "key123"

    def test_process_response_is_noop(self):
        """Test that process_response does nothing"""
        auth_strategy = BearerTokenAuth("token")
        middleware = AuthMiddleware(auth_strategy)

        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.headers = {}
        mock_resp.content = b""
        mock_resp.text = ""
        mock_resp.url = "http://test.com"
        mock_resp.elapsed = timedelta(milliseconds=100)

        response = Response.from_requests_response(mock_resp)
        result = middleware.process_response(response)

        assert result is response

    def test_middleware_returns_request(self):
        """Test that middleware returns the request"""
        auth_strategy = BearerTokenAuth("token")
        middleware = AuthMiddleware(auth_strategy)
        request = Request(method="GET", url="http://test.com")

        result = middleware.process_request(request)

        assert result is request

    def test_repr_shows_strategy(self):
        """Test __repr__ includes strategy information"""
        auth_strategy = BearerTokenAuth("token")
        middleware = AuthMiddleware(auth_strategy)

        repr_str = repr(middleware)

        assert "AuthMiddleware" in repr_str
        assert "BearerTokenAuth" in repr_str


class TestAuthMiddlewareIntegration:
    """Integration tests with HTTPClient"""

    @pytest.mark.integration
    def test_auth_middleware_in_pipeline(self):
        """Test auth middleware works in middleware pipeline"""
        from http_client.middleware import MiddlewarePipeline

        auth_strategy = BearerTokenAuth("integration_token")
        middleware = AuthMiddleware(auth_strategy)

        pipeline = MiddlewarePipeline()
        pipeline.add(middleware)

        request = Request(method="GET", url="http://test.com")
        result = pipeline.execute_request(request)

        assert result.headers["Authorization"] == "Bearer integration_token"

    @pytest.mark.integration
    def test_multiple_middlewares_with_auth(self):
        """Test auth middleware works with other middlewares"""
        from http_client.middleware import MiddlewarePipeline
        from http_client.middlewares.logging import LoggingMiddleware

        auth_strategy = BearerTokenAuth("token123")
        auth_middleware = AuthMiddleware(auth_strategy)
        logging_middleware = LoggingMiddleware()

        pipeline = MiddlewarePipeline()
        pipeline.add(logging_middleware)
        pipeline.add(auth_middleware)

        request = Request(method="GET", url="http://test.com")
        result = pipeline.execute_request(request)

        # Auth should be applied
        assert result.headers["Authorization"] == "Bearer token123"

    @pytest.mark.integration
    def test_auth_middleware_with_builder(self):
        """Test using with_auth() builder method"""
        from http_client import HTTPClient

        # Create client using builder with auth
        auth_strategy = BearerTokenAuth("builder_test_token")
        client = (
            HTTPClient.builder()
            .base_url("https://api.example.com")
            .with_auth(auth_strategy)
            .build()
        )

        # Verify auth middleware was added to pipeline
        assert client.pipeline.head is not None

        # Create a request and process it through the pipeline
        request = Request(method="GET", url="https://api.example.com/test")
        processed_request = client.pipeline.execute_request(request)

        # Verify auth was applied
        assert "Authorization" in processed_request.headers
        assert processed_request.headers["Authorization"] == "Bearer builder_test_token"

    @pytest.mark.integration
    def test_auth_with_multiple_middlewares(self):
        """Test auth middleware works alongside other middlewares in builder"""
        from http_client import HTTPClient
        from http_client.middlewares.logging import LoggingMiddleware

        # Build client with both logging and auth
        auth_strategy = BasicAuth("user", "pass")
        client = (
            HTTPClient.builder()
            .base_url("https://api.example.com")
            .add_middleware(LoggingMiddleware())
            .with_auth(auth_strategy)
            .build()
        )

        # Create and process request
        request = Request(method="GET", url="https://api.example.com/test")
        processed_request = client.pipeline.execute_request(request)

        # Verify auth was applied
        assert "Authorization" in processed_request.headers
        assert processed_request.headers["Authorization"].startswith("Basic ")

    @pytest.mark.integration
    def test_auth_with_api_key_query_param(self):
        """Test API key auth in query params via builder"""
        from http_client import HTTPClient

        auth_strategy = APIKeyAuth("secret123", location="query", param_name="api_key")
        client = HTTPClient.builder().with_auth(auth_strategy).build()

        # Create and process request
        request = Request(method="GET", url="https://api.example.com/test")
        processed_request = client.pipeline.execute_request(request)

        # Verify API key was added to params
        assert "api_key" in processed_request.params
        assert processed_request.params["api_key"] == "secret123"
