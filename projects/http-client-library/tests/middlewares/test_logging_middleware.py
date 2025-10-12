"""
Tests for logging middleware.

Pattern: Chain of Responsibility (concrete implementation test)
"""

import logging
from datetime import timedelta
from unittest.mock import Mock, patch

from http_client.middlewares.logging import HeaderMiddleware, LoggingMiddleware
from http_client.models import Request, Response


class TestLoggingMiddleware:
    """Test LoggingMiddleware"""

    def test_initialization_with_default_log_level(self):
        """Test middleware initializes with default INFO level"""
        middleware = LoggingMiddleware()
        assert middleware.log_level == logging.INFO

    def test_initialization_with_custom_log_level(self):
        """Test middleware initializes with custom log level"""
        middleware = LoggingMiddleware(log_level=logging.DEBUG)
        assert middleware.log_level == logging.DEBUG

    def test_process_request_logs_message(self):
        """Test that process_request logs the request"""
        middleware = LoggingMiddleware()
        request = Request(method="GET", url="http://test.com/api/users")

        with patch("http_client.middlewares.logging.logger") as mock_logger:
            result = middleware.process_request(request)

            # Verify logging was called
            mock_logger.log.assert_called_once()
            call_args = mock_logger.log.call_args

            # Check log level
            assert call_args[0][0] == logging.INFO

            # Check log message contains method and URL
            log_message = call_args[0][1]
            assert "GET" in log_message
            assert "http://test.com/api/users" in log_message

            # Verify request is returned unchanged
            assert result == request

    def test_process_request_with_custom_log_level(self):
        """Test that custom log level is used"""
        middleware = LoggingMiddleware(log_level=logging.DEBUG)
        request = Request(method="POST", url="http://test.com/api/create")

        with patch("http_client.middlewares.logging.logger") as mock_logger:
            middleware.process_request(request)

            # Verify DEBUG level was used
            call_args = mock_logger.log.call_args
            assert call_args[0][0] == logging.DEBUG

    def test_process_request_does_not_modify_request(self):
        """Test that process_request returns request unchanged"""
        middleware = LoggingMiddleware()
        request = Request(
            method="POST",
            url="http://test.com/api/data",
            headers={"Content-Type": "application/json"},
            params={"q": "test"},
        )

        with patch("http_client.middlewares.logging.logger"):
            result = middleware.process_request(request)

            assert result is request
            assert result.method == "POST"
            assert result.url == "http://test.com/api/data"
            assert result.headers == {"Content-Type": "application/json"}
            assert result.params == {"q": "test"}

    def test_process_response_logs_message(self):
        """Test that process_response logs the response"""
        middleware = LoggingMiddleware()

        # Create mock response
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.headers = {"Content-Type": "application/json"}
        mock_resp.content = b'{"key": "value"}'
        mock_resp.text = '{"key": "value"}'
        mock_resp.url = "http://test.com/api/users"
        mock_resp.elapsed = timedelta(milliseconds=150)

        response = Response.from_requests_response(mock_resp)

        with patch("http_client.middlewares.logging.logger") as mock_logger:
            result = middleware.process_response(response)

            # Verify logging was called
            mock_logger.log.assert_called_once()
            call_args = mock_logger.log.call_args

            # Check log level
            assert call_args[0][0] == logging.INFO

            # Check log message contains status, URL, and elapsed time
            log_message = call_args[0][1]
            assert "200" in log_message
            assert "http://test.com/api/users" in log_message
            assert "150.00ms" in log_message or "150ms" in log_message

            # Verify response is returned unchanged
            assert result == response

    def test_process_response_does_not_modify_response(self):
        """Test that process_response returns response unchanged"""
        middleware = LoggingMiddleware()

        mock_resp = Mock()
        mock_resp.status_code = 404
        mock_resp.headers = {"Content-Type": "text/html"}
        mock_resp.content = b"Not Found"
        mock_resp.text = "Not Found"
        mock_resp.url = "http://test.com/notfound"
        mock_resp.elapsed = timedelta(milliseconds=50)

        response = Response.from_requests_response(mock_resp)

        with patch("http_client.middlewares.logging.logger"):
            result = middleware.process_response(response)

            assert result is response
            assert result.status_code == 404
            assert result.url == "http://test.com/notfound"

    def test_process_response_formats_elapsed_time_correctly(self):
        """Test that elapsed time is formatted with 2 decimal places"""
        middleware = LoggingMiddleware()

        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.headers = {}
        mock_resp.content = b""
        mock_resp.text = ""
        mock_resp.url = "http://test.com"
        mock_resp.elapsed = timedelta(milliseconds=123.456)  # Should format as 123.46ms

        response = Response.from_requests_response(mock_resp)

        with patch("http_client.middlewares.logging.logger") as mock_logger:
            middleware.process_response(response)

            log_message = mock_logger.log.call_args[0][1]
            # Check that elapsed time is formatted
            assert "ms" in log_message

    def test_logging_middleware_arrow_symbols(self):
        """Test that log messages use arrow symbols for direction"""
        middleware = LoggingMiddleware()
        request = Request(method="GET", url="http://test.com")

        with patch("http_client.middlewares.logging.logger") as mock_logger:
            middleware.process_request(request)

            log_message = mock_logger.log.call_args[0][1]
            # Should start with → (right arrow) for outgoing request
            assert log_message.startswith("→") or log_message.startswith("->")

    def test_logging_different_http_methods(self):
        """Test logging works with different HTTP methods"""
        middleware = LoggingMiddleware()
        methods = ["GET", "POST", "PUT", "DELETE", "PATCH"]

        for method in methods:
            request = Request(method=method, url="http://test.com")

            with patch("http_client.middlewares.logging.logger") as mock_logger:
                middleware.process_request(request)

                log_message = mock_logger.log.call_args[0][1]
                assert method in log_message


class TestHeaderMiddleware:
    """Test HeaderMiddleware"""

    def test_initialization(self):
        """Test middleware initializes with headers"""
        headers = {"Authorization": "Bearer token123", "User-Agent": "MyClient"}
        middleware = HeaderMiddleware(headers)

        assert middleware.headers == headers

    def test_process_request_adds_headers(self):
        """Test that process_request adds custom headers"""
        middleware = HeaderMiddleware({"X-Custom-Header": "CustomValue"})
        request = Request(method="GET", url="http://test.com")

        result = middleware.process_request(request)

        assert "X-Custom-Header" in result.headers
        assert result.headers["X-Custom-Header"] == "CustomValue"

    def test_process_request_adds_multiple_headers(self):
        """Test adding multiple headers at once"""
        headers = {
            "Authorization": "Bearer token123",
            "User-Agent": "MyClient/1.0",
            "X-API-Key": "secret",
        }
        middleware = HeaderMiddleware(headers)
        request = Request(method="GET", url="http://test.com")

        result = middleware.process_request(request)

        assert result.headers["Authorization"] == "Bearer token123"
        assert result.headers["User-Agent"] == "MyClient/1.0"
        assert result.headers["X-API-Key"] == "secret"

    def test_process_request_preserves_existing_headers(self):
        """Test that existing headers are not removed"""
        middleware = HeaderMiddleware({"X-Custom": "value"})
        request = Request(
            method="GET", url="http://test.com", headers={"Content-Type": "application/json"}
        )

        result = middleware.process_request(request)

        # Both headers should be present
        assert result.headers["Content-Type"] == "application/json"
        assert result.headers["X-Custom"] == "value"

    def test_process_request_overwrites_existing_header(self):
        """Test that middleware headers overwrite existing headers with same key"""
        middleware = HeaderMiddleware({"Content-Type": "text/plain"})
        request = Request(
            method="GET", url="http://test.com", headers={"Content-Type": "application/json"}
        )

        result = middleware.process_request(request)

        # Middleware header should overwrite
        assert result.headers["Content-Type"] == "text/plain"

    def test_process_response_is_noop(self):
        """Test that process_response does nothing"""
        middleware = HeaderMiddleware({"X-Custom": "value"})

        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.headers = {}
        mock_resp.content = b""
        mock_resp.text = ""
        mock_resp.url = "http://test.com"
        mock_resp.elapsed = timedelta(milliseconds=100)

        response = Response.from_requests_response(mock_resp)
        result = middleware.process_response(response)

        # Response should be returned unchanged
        assert result is response
        assert result.status_code == 200

    def test_empty_headers_initialization(self):
        """Test middleware can be initialized with empty headers dict"""
        middleware = HeaderMiddleware({})
        request = Request(method="GET", url="http://test.com")

        result = middleware.process_request(request)

        # Request should be unchanged
        assert result.headers == {}

    def test_header_middleware_modifies_request_in_place(self):
        """Test that HeaderMiddleware modifies request headers in place"""
        middleware = HeaderMiddleware({"X-Test": "value"})
        request = Request(method="GET", url="http://test.com")

        result = middleware.process_request(request)

        # Should return the same request object (modified in place)
        assert result is request
        assert request.headers["X-Test"] == "value"


class TestMiddlewareIntegration:
    """Test integration between different middlewares"""

    def test_logging_and_header_middleware_together(self):
        """Test that LoggingMiddleware and HeaderMiddleware work together"""
        header_middleware = HeaderMiddleware({"Authorization": "Bearer token"})
        logging_middleware = LoggingMiddleware()

        # Chain them
        header_middleware.set_next(logging_middleware)

        request = Request(method="GET", url="http://test.com")

        with patch("http_client.middlewares.logging.logger"):
            # Process through header middleware first
            result = header_middleware.handle_request(request)

            # Header should be added
            assert result.headers["Authorization"] == "Bearer token"

    def test_multiple_header_middlewares_chain(self):
        """Test chaining multiple HeaderMiddleware instances"""
        mw1 = HeaderMiddleware({"X-Header-1": "value1"})
        mw2 = HeaderMiddleware({"X-Header-2": "value2"})
        mw3 = HeaderMiddleware({"X-Header-3": "value3"})

        # Chain them
        mw1.set_next(mw2)
        mw2.set_next(mw3)

        request = Request(method="GET", url="http://test.com")
        result = mw1.handle_request(request)

        # All headers should be present
        assert result.headers["X-Header-1"] == "value1"
        assert result.headers["X-Header-2"] == "value2"
        assert result.headers["X-Header-3"] == "value3"
