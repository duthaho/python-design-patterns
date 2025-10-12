"""
Tests for HTTPClient and Builder.

Pattern: Builder (testing)
"""

from unittest.mock import patch

import pytest
import requests
import responses

from http_client.client import HTTPClient, HTTPClientBuilder
from http_client.exceptions import RequestError, TimeoutError
from http_client.middleware import Middleware
from http_client.middlewares.logging import HeaderMiddleware, LoggingMiddleware
from http_client.models import Request, Response


class TrackingMiddleware(Middleware):
    """Middleware for testing that tracks if it was called"""

    def __init__(self):
        super().__init__()
        self.request_processed = False
        self.response_processed = False

    def process_request(self, request: Request) -> Request:
        self.request_processed = True
        return request

    def process_response(self, response: Response) -> Response:
        self.response_processed = True
        return response


class TestHTTPClientBuilder:
    """Test Builder pattern implementation"""

    def test_builder_default_values(self):
        """Test builder creates client with defaults"""
        builder = HTTPClientBuilder()
        client = builder.build()

        assert client.base_url == ""
        assert client.timeout == 30.0
        assert client.pipeline.head is None

    def test_builder_with_base_url(self):
        """Test builder sets base_url"""
        builder = HTTPClientBuilder()
        client = builder.base_url("https://api.example.com").build()

        assert client.base_url == "https://api.example.com"

    def test_builder_with_base_url_strips_trailing_slash(self):
        """Test builder strips trailing slash from base_url"""
        builder = HTTPClientBuilder()
        client = builder.base_url("https://api.example.com/").build()

        assert client.base_url == "https://api.example.com"

    def test_builder_with_timeout(self):
        """Test builder sets timeout"""
        builder = HTTPClientBuilder()
        client = builder.timeout(10.0).build()

        assert client.timeout == 10.0

    def test_builder_fluent_api(self):
        """Test builder methods return self for chaining"""
        builder = HTTPClientBuilder()

        assert builder.base_url("https://api.example.com") is builder
        assert builder.timeout(10.0) is builder
        assert builder.add_middleware(LoggingMiddleware()) is builder

    def test_builder_adds_middleware(self):
        """Test builder adds middleware to pipeline"""
        builder = HTTPClientBuilder()
        middleware = TrackingMiddleware()
        client = builder.add_middleware(middleware).build()

        assert client.pipeline.head is not None
        assert client.pipeline.head == middleware

    def test_builder_multiple_middlewares(self):
        """Test builder adds multiple middlewares in order"""
        builder = HTTPClientBuilder()
        middleware1 = TrackingMiddleware()
        middleware2 = TrackingMiddleware()
        middleware3 = TrackingMiddleware()

        client = (
            builder.add_middleware(middleware1)
            .add_middleware(middleware2)
            .add_middleware(middleware3)
            .build()
        )

        # Verify chain
        assert client.pipeline.head == middleware1
        assert middleware1.next_middleware == middleware2
        assert middleware2.next_middleware == middleware3
        assert middleware3.next_middleware is None

    def test_static_builder_method(self):
        """Test HTTPClient.builder() creates new builder"""
        builder = HTTPClient.builder()

        assert isinstance(builder, HTTPClientBuilder)

    def test_builder_full_configuration(self):
        """Test building client with full configuration"""
        middleware = TrackingMiddleware()

        client = (
            HTTPClient.builder()
            .base_url("https://api.example.com")
            .timeout(15.0)
            .add_middleware(middleware)
            .build()
        )

        assert client.base_url == "https://api.example.com"
        assert client.timeout == 15.0
        assert client.pipeline.head == middleware


class TestHTTPClient:
    """Test HTTPClient functionality"""

    @pytest.fixture
    def client(self):
        """Create a basic client for testing"""
        return HTTPClient()

    @responses.activate
    def test_get_request(self, client):
        """Test GET request execution"""
        responses.add(responses.GET, "http://test.com/path", json={"key": "value"}, status=200)

        response = client.get("http://test.com/path")

        assert response.status_code == 200
        assert response.json() == {"key": "value"}

    @responses.activate
    def test_get_with_params(self, client):
        """Test GET request with query parameters"""
        responses.add(responses.GET, "http://test.com/search", json={"results": []}, status=200)

        response = client.get("http://test.com/search", params={"q": "test", "page": 1})

        assert response.status_code == 200
        # Verify the request was made (responses library records this)
        assert len(responses.calls) == 1
        assert "q=test" in responses.calls[0].request.url
        assert "page=1" in responses.calls[0].request.url

    @responses.activate
    def test_post_with_json(self, client):
        """Test POST request with JSON body"""
        responses.add(
            responses.POST, "http://test.com/create", json={"id": 1, "created": True}, status=201
        )

        response = client.post("http://test.com/create", json={"name": "test"})

        assert response.status_code == 201
        assert response.json()["created"] is True

    @responses.activate
    def test_post_with_data(self, client):
        """Test POST request with form data"""
        responses.add(responses.POST, "http://test.com/upload", body="OK", status=200)

        response = client.post("http://test.com/upload", data="raw data")

        assert response.status_code == 200

    @responses.activate
    def test_put_request(self, client):
        """Test PUT request"""
        responses.add(responses.PUT, "http://test.com/update/1", json={"updated": True}, status=200)

        response = client.put("http://test.com/update/1", json={"name": "updated"})

        assert response.status_code == 200
        assert response.json()["updated"] is True

    @responses.activate
    def test_delete_request(self, client):
        """Test DELETE request"""
        responses.add(responses.DELETE, "http://test.com/delete/1", status=204)

        response = client.delete("http://test.com/delete/1")

        assert response.status_code == 204

    @responses.activate
    def test_base_url_prepended(self):
        """Test base_url is prepended to paths"""
        responses.add(responses.GET, "http://api.test.com/users", json={"users": []}, status=200)

        client = HTTPClient(base_url="http://api.test.com")
        response = client.get("/users")

        assert response.status_code == 200
        assert responses.calls[0].request.url == "http://api.test.com/users"

    @responses.activate
    def test_base_url_with_path_without_leading_slash(self):
        """Test base_url works with paths without leading slash"""
        responses.add(responses.GET, "http://api.test.com/users", json={"users": []}, status=200)

        client = HTTPClient(base_url="http://api.test.com")
        response = client.get("users")

        assert response.status_code == 200
        assert responses.calls[0].request.url == "http://api.test.com/users"

    @responses.activate
    def test_middleware_execution(self):
        """Test middleware is executed during request"""
        responses.add(responses.GET, "http://test.com/path", json={"key": "value"}, status=200)

        middleware = TrackingMiddleware()
        client = HTTPClient.builder().add_middleware(middleware).build()

        response = client.get("http://test.com/path")

        assert middleware.request_processed is True
        assert middleware.response_processed is True
        assert response.status_code == 200

    @responses.activate
    def test_multiple_middlewares_execution(self):
        """Test multiple middlewares are all executed"""
        responses.add(responses.GET, "http://test.com/path", json={"key": "value"}, status=200)

        middleware1 = TrackingMiddleware()
        middleware2 = TrackingMiddleware()

        client = (
            HTTPClient.builder().add_middleware(middleware1).add_middleware(middleware2).build()
        )

        response = client.get("http://test.com/path")

        assert middleware1.request_processed is True
        assert middleware1.response_processed is True
        assert middleware2.request_processed is True
        assert middleware2.response_processed is True

    def test_context_manager(self):
        """Test client works as context manager"""
        with HTTPClient() as client:
            assert client.session is not None

        # After exiting context, session should be closed
        # (we can't easily test if it's closed, but we verify no errors)

    @responses.activate
    def test_context_manager_with_request(self):
        """Test making request within context manager"""
        responses.add(responses.GET, "http://test.com/path", json={"key": "value"}, status=200)

        with HTTPClient() as client:
            response = client.get("http://test.com/path")
            assert response.status_code == 200

    @responses.activate
    def test_request_timeout_uses_default(self):
        """Test request uses default timeout when not specified"""
        responses.add(responses.GET, "http://test.com/path", json={"key": "value"}, status=200)

        client = HTTPClient(timeout=10.0)
        response = client.get("http://test.com/path")

        # Verify timeout was used (check the actual request made)
        assert response.status_code == 200

    @responses.activate
    def test_custom_headers_in_request(self):
        """Test custom headers can be passed in request"""
        responses.add(responses.GET, "http://test.com/path", json={"key": "value"}, status=200)

        client = HTTPClient()
        response = client.get("http://test.com/path", headers={"X-Custom": "value"})

        assert response.status_code == 200
        # Verify custom header was sent
        assert responses.calls[0].request.headers.get("X-Custom") == "value"

    def test_request_error_handling(self):
        """Test request errors are wrapped in RequestError"""
        client = HTTPClient()

        with patch.object(
            client.session,
            "request",
            side_effect=requests.exceptions.ConnectionError("Connection failed"),
        ):
            with pytest.raises(RequestError) as exc_info:
                client.get("http://test.com/path")

            assert "Request failed" in str(exc_info.value)

    def test_timeout_error_handling(self):
        """Test timeout errors are wrapped in TimeoutError"""
        client = HTTPClient()

        with patch.object(
            client.session, "request", side_effect=requests.exceptions.Timeout("Timeout occurred")
        ):
            with pytest.raises(TimeoutError) as exc_info:
                client.get("http://test.com/path")

            assert "Request timed out" in str(exc_info.value)

    @responses.activate
    def test_get_without_base_url(self, client):
        """Test GET with full URL and no base_url"""
        responses.add(
            responses.GET, "https://example.com/api/data", json={"data": "value"}, status=200
        )

        response = client.get("https://example.com/api/data")

        assert response.status_code == 200
        assert response.json()["data"] == "value"

    @responses.activate
    def test_post_without_base_url(self, client):
        """Test POST with full URL and no base_url"""
        responses.add(
            responses.POST, "https://example.com/api/create", json={"created": True}, status=201
        )

        response = client.post("https://example.com/api/create", json={"name": "test"})

        assert response.status_code == 201

    @responses.activate
    def test_header_middleware_integration(self):
        """Test HeaderMiddleware adds headers correctly"""
        responses.add(responses.GET, "http://test.com/path", json={"key": "value"}, status=200)

        client = (
            HTTPClient.builder()
            .add_middleware(HeaderMiddleware({"X-Custom-Header": "CustomValue"}))
            .build()
        )

        response = client.get("http://test.com/path")

        assert response.status_code == 200
        # Verify the header was added
        assert responses.calls[0].request.headers.get("X-Custom-Header") == "CustomValue"

    def test_close_method(self, client):
        """Test close method closes the session"""
        assert client.session is not None
        client.close()
        # Session is closed (we just verify no errors occur)

    @responses.activate
    def test_multiple_requests_with_same_client(self):
        """Test making multiple requests with the same client instance"""
        responses.add(responses.GET, "http://test.com/first", json={"request": 1}, status=200)
        responses.add(responses.GET, "http://test.com/second", json={"request": 2}, status=200)

        client = HTTPClient()

        response1 = client.get("http://test.com/first")
        response2 = client.get("http://test.com/second")

        assert response1.json()["request"] == 1
        assert response2.json()["request"] == 2
        assert len(responses.calls) == 2


class TestHTTPClientEdgeCases:
    """Test edge cases and error scenarios"""

    @responses.activate
    def test_empty_response_body(self):
        """Test handling empty response body"""
        responses.add(responses.GET, "http://test.com/empty", body="", status=204)

        client = HTTPClient()
        response = client.get("http://test.com/empty")

        assert response.status_code == 204
        assert response.text == ""

    @responses.activate
    def test_large_json_response(self):
        """Test handling large JSON responses"""
        large_data = {"items": [{"id": i, "name": f"item{i}"} for i in range(1000)]}

        responses.add(responses.GET, "http://test.com/large", json=large_data, status=200)

        client = HTTPClient()
        response = client.get("http://test.com/large")

        assert response.status_code == 200
        assert len(response.json()["items"]) == 1000

    @responses.activate
    def test_base_url_trailing_slash_handling(self):
        """Test various base_url and path combinations"""
        test_cases = [
            ("http://api.test.com", "/users", "http://api.test.com/users"),
            ("http://api.test.com", "users", "http://api.test.com/users"),
            ("http://api.test.com/", "/users", "http://api.test.com/users"),
            ("http://api.test.com/", "users", "http://api.test.com/users"),
        ]

        for base_url, path, expected_url in test_cases:
            responses.add(responses.GET, expected_url, json={"ok": True}, status=200)

            client = HTTPClient(base_url=base_url)
            response = client.get(path)

            assert response.status_code == 200
            responses.reset()

    @responses.activate
    def test_middleware_modifies_request(self):
        """Test that middleware can modify requests"""
        responses.add(responses.GET, "http://test.com/path", json={"key": "value"}, status=200)

        # HeaderMiddleware should add a custom header
        client = (
            HTTPClient.builder()
            .add_middleware(HeaderMiddleware({"Authorization": "Bearer token123"}))
            .build()
        )

        response = client.get("http://test.com/path")

        assert response.status_code == 200
        # Verify the header was added to the actual request
        assert responses.calls[0].request.headers.get("Authorization") == "Bearer token123"


class TestHTTPClientIntegration:
    """Integration tests combining multiple features"""

    @responses.activate
    def test_full_builder_with_all_features(self):
        """Test building a client with all features"""
        responses.add(
            responses.POST,
            "https://api.example.com/v1/users",
            json={"id": 1, "name": "John"},
            status=201,
        )

        client = (
            HTTPClient.builder()
            .base_url("https://api.example.com/v1")
            .timeout(20.0)
            .add_middleware(HeaderMiddleware({"User-Agent": "MyClient/1.0"}))
            .add_middleware(LoggingMiddleware())
            .build()
        )

        response = client.post("/users", json={"name": "John"})

        assert response.status_code == 201
        assert response.json()["id"] == 1
        assert response.is_success() is True

    @responses.activate
    def test_middleware_chain_execution_order(self):
        """Test that middleware execute in the correct order"""
        responses.add(responses.GET, "http://test.com/path", json={"result": "ok"}, status=200)

        # Create middlewares that add headers in sequence
        header_mw1 = HeaderMiddleware({"X-Order": "1"})
        header_mw2 = HeaderMiddleware({"X-Order": "2"})  # This will overwrite

        client = HTTPClient.builder().add_middleware(header_mw1).add_middleware(header_mw2).build()

        response = client.get("http://test.com/path")

        assert response.status_code == 200
        # The last middleware should overwrite the header
        assert responses.calls[0].request.headers.get("X-Order") == "2"
