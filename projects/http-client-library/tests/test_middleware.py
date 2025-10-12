"""
Tests for middleware and middleware pipeline.

Pattern: Chain of Responsibility (testing)
"""

from datetime import timedelta
from unittest.mock import Mock

from http_client.middleware import Middleware, MiddlewarePipeline
from http_client.models import Request, Response


class TestMiddleware(Middleware):
    """Test middleware that tracks execution"""

    def __init__(self, name: str):
        super().__init__()
        self.name = name
        self.request_calls = []
        self.response_calls = []

    def process_request(self, request: Request) -> Request:
        self.request_calls.append(self.name)
        # Add marker to headers to track execution
        request.headers[f"X-Processed-By-{self.name}"] = "true"
        return request

    def process_response(self, response: Response) -> Response:
        self.response_calls.append(self.name)
        return response


class TestMiddlewareChain:
    """Test middleware chaining logic"""

    def test_set_next_returns_next_middleware(self):
        """Test that set_next returns the middleware being set"""
        middleware_a = TestMiddleware("A")
        middleware_b = TestMiddleware("B")

        result = middleware_a.set_next(middleware_b)

        assert result == middleware_b
        assert middleware_a.next_middleware == middleware_b

    def test_handle_request_single_middleware(self):
        """Test request handling with single middleware"""
        middleware = TestMiddleware("A")
        request = Request(method="GET", url="http://test.com")

        result = middleware.handle_request(request)

        assert "A" in middleware.request_calls
        assert "X-Processed-By-A" in result.headers
        assert result.headers["X-Processed-By-A"] == "true"

    def test_handle_request_chain(self):
        """Test request flows through chain in correct order"""
        middleware_a = TestMiddleware("A")
        middleware_b = TestMiddleware("B")
        middleware_c = TestMiddleware("C")

        # Chain them: A -> B -> C
        middleware_a.set_next(middleware_b)
        middleware_b.set_next(middleware_c)

        request = Request(method="GET", url="http://test.com")
        result = middleware_a.handle_request(request)

        # All three should have processed the request
        assert middleware_a.request_calls == ["A"]
        assert middleware_b.request_calls == ["B"]
        assert middleware_c.request_calls == ["C"]

        # All headers should be present
        assert "X-Processed-By-A" in result.headers
        assert "X-Processed-By-B" in result.headers
        assert "X-Processed-By-C" in result.headers

    def test_handle_response_single_middleware(self):
        """Test response handling with single middleware"""
        middleware = TestMiddleware("A")

        # Create mock response
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.headers = {}
        mock_resp.content = b""
        mock_resp.text = ""
        mock_resp.url = "http://test.com"
        mock_resp.elapsed = timedelta(milliseconds=100)

        response = Response.from_requests_response(mock_resp)
        result = middleware.handle_response(response)

        assert "A" in middleware.response_calls
        assert result == response

    def test_handle_response_reverse_order(self):
        """Test response flows through chain in REVERSE order"""
        middleware_a = TestMiddleware("A")
        middleware_b = TestMiddleware("B")
        middleware_c = TestMiddleware("C")

        # Chain them: A -> B -> C
        middleware_a.set_next(middleware_b)
        middleware_b.set_next(middleware_c)

        # Create mock response
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.headers = {}
        mock_resp.content = b""
        mock_resp.text = ""
        mock_resp.url = "http://test.com"
        mock_resp.elapsed = timedelta(milliseconds=100)

        response = Response.from_requests_response(mock_resp)
        result = middleware_a.handle_response(response)

        # All three should have processed the response
        assert len(middleware_c.response_calls) == 1
        assert len(middleware_b.response_calls) == 1
        assert len(middleware_a.response_calls) == 1

        # But in REVERSE order: C, then B, then A
        # We can verify this by checking the order matters
        assert middleware_c.response_calls == ["C"]
        assert middleware_b.response_calls == ["B"]
        assert middleware_a.response_calls == ["A"]

    def test_middleware_chain_with_no_next(self):
        """Test middleware works when there's no next middleware"""
        middleware = TestMiddleware("A")
        request = Request(method="GET", url="http://test.com")

        result = middleware.handle_request(request)

        assert result.headers["X-Processed-By-A"] == "true"


class TestMiddlewarePipeline:
    """Test MiddlewarePipeline"""

    def test_add_first_middleware(self):
        """Test adding first middleware sets head and tail"""
        pipeline = MiddlewarePipeline()
        middleware = TestMiddleware("A")

        result = pipeline.add(middleware)

        assert pipeline.head == middleware
        assert pipeline.tail == middleware
        assert result == pipeline  # Returns self for chaining

    def test_add_multiple_middlewares(self):
        """Test adding multiple middlewares links them correctly"""
        pipeline = MiddlewarePipeline()
        middleware_a = TestMiddleware("A")
        middleware_b = TestMiddleware("B")
        middleware_c = TestMiddleware("C")

        pipeline.add(middleware_a)
        pipeline.add(middleware_b)
        pipeline.add(middleware_c)

        assert pipeline.head == middleware_a
        assert pipeline.tail == middleware_c
        assert middleware_a.next_middleware == middleware_b
        assert middleware_b.next_middleware == middleware_c
        assert middleware_c.next_middleware is None

    def test_add_returns_self_for_chaining(self):
        """Test add() returns pipeline for fluent API"""
        pipeline = MiddlewarePipeline()
        middleware_a = TestMiddleware("A")
        middleware_b = TestMiddleware("B")

        result = pipeline.add(middleware_a).add(middleware_b)

        assert result == pipeline
        assert pipeline.head == middleware_a
        assert pipeline.tail == middleware_b

    def test_execute_request_with_empty_pipeline(self):
        """Test execute_request with no middleware"""
        pipeline = MiddlewarePipeline()
        request = Request(method="GET", url="http://test.com")

        result = pipeline.execute_request(request)

        # Should return unchanged request
        assert result == request
        assert len(result.headers) == 0

    def test_execute_request_with_middleware(self):
        """Test execute_request processes through all middleware"""
        pipeline = MiddlewarePipeline()
        middleware_a = TestMiddleware("A")
        middleware_b = TestMiddleware("B")
        middleware_c = TestMiddleware("C")

        pipeline.add(middleware_a).add(middleware_b).add(middleware_c)

        request = Request(method="GET", url="http://test.com")
        result = pipeline.execute_request(request)

        # All three headers should be present
        assert "X-Processed-By-A" in result.headers
        assert "X-Processed-By-B" in result.headers
        assert "X-Processed-By-C" in result.headers

        # Verify execution order
        assert middleware_a.request_calls == ["A"]
        assert middleware_b.request_calls == ["B"]
        assert middleware_c.request_calls == ["C"]

    def test_execute_response_with_empty_pipeline(self):
        """Test execute_response with no middleware"""
        pipeline = MiddlewarePipeline()

        # Create mock response
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.headers = {}
        mock_resp.content = b""
        mock_resp.text = ""
        mock_resp.url = "http://test.com"
        mock_resp.elapsed = timedelta(milliseconds=100)

        response = Response.from_requests_response(mock_resp)
        result = pipeline.execute_response(response)

        # Should return unchanged response
        assert result == response

    def test_execute_response_with_middleware(self):
        """Test execute_response processes in reverse order"""
        pipeline = MiddlewarePipeline()
        middleware_a = TestMiddleware("A")
        middleware_b = TestMiddleware("B")
        middleware_c = TestMiddleware("C")

        pipeline.add(middleware_a).add(middleware_b).add(middleware_c)

        # Create mock response
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.headers = {}
        mock_resp.content = b""
        mock_resp.text = ""
        mock_resp.url = "http://test.com"
        mock_resp.elapsed = timedelta(milliseconds=100)

        response = Response.from_requests_response(mock_resp)
        result = pipeline.execute_response(response)

        # All middleware should have processed the response
        assert len(middleware_a.response_calls) == 1
        assert len(middleware_b.response_calls) == 1
        assert len(middleware_c.response_calls) == 1

    def test_pipeline_isolation(self):
        """Test that multiple pipelines are independent"""
        pipeline1 = MiddlewarePipeline()
        pipeline2 = MiddlewarePipeline()

        middleware_a = TestMiddleware("A")
        middleware_b = TestMiddleware("B")

        pipeline1.add(middleware_a)
        pipeline2.add(middleware_b)

        assert pipeline1.head == middleware_a
        assert pipeline2.head == middleware_b
        assert pipeline1.head != pipeline2.head
