"""
Tests for Request and Response models.
"""

from datetime import timedelta
from unittest.mock import Mock

import pytest

from http_client.models import Request, Response


class TestRequest:
    """Test Request model"""

    def test_request_creation_with_defaults(self):
        """Test creating request with minimal parameters"""
        request = Request(method="GET", url="http://test.com")

        assert request.method == "GET"
        assert request.url == "http://test.com"
        assert request.headers == {}
        assert request.params == {}
        assert request.data is None
        assert request.json is None
        assert request.timeout is None

    def test_request_with_all_parameters(self):
        """Test creating request with all parameters"""
        request = Request(
            method="POST",
            url="http://test.com/api",
            headers={"Content-Type": "application/json"},
            params={"q": "search"},
            data="raw data",
            json={"key": "value"},
            timeout=30.0,
        )

        assert request.method == "POST"
        assert request.url == "http://test.com/api"
        assert request.headers == {"Content-Type": "application/json"}
        assert request.params == {"q": "search"}
        assert request.data == "raw data"
        assert request.json == {"key": "value"}
        assert request.timeout == 30.0

    def test_to_requests_kwargs_minimal(self):
        """Test conversion to requests kwargs with minimal params"""
        request = Request(method="GET", url="http://test.com")
        kwargs = request.to_requests_kwargs()

        assert kwargs["method"] == "GET"
        assert kwargs["url"] == "http://test.com"
        assert kwargs["headers"] == {}
        assert kwargs["params"] == {}
        # timeout is None, so should be filtered out
        assert "timeout" not in kwargs

    def test_to_requests_kwargs_with_json(self):
        """Test conversion includes json parameter"""
        request = Request(method="POST", url="http://test.com", json={"key": "value"})
        kwargs = request.to_requests_kwargs()

        assert "json" in kwargs
        assert kwargs["json"] == {"key": "value"}
        # data should NOT be in kwargs when json is present
        assert "data" not in kwargs

    def test_to_requests_kwargs_with_data(self):
        """Test conversion includes data parameter"""
        request = Request(method="POST", url="http://test.com", data="raw data")
        kwargs = request.to_requests_kwargs()

        assert "data" in kwargs
        assert kwargs["data"] == "raw data"
        # json should NOT be in kwargs when only data is present
        assert "json" not in kwargs

    def test_to_requests_kwargs_filters_none_values(self):
        """Test that None values are filtered out"""
        request = Request(method="GET", url="http://test.com", timeout=None)
        kwargs = request.to_requests_kwargs()

        # None values should be filtered out
        assert "timeout" not in kwargs
        assert "data" not in kwargs
        assert "json" not in kwargs

    def test_to_requests_kwargs_with_timeout(self):
        """Test timeout is included when set"""
        request = Request(method="GET", url="http://test.com", timeout=30.0)
        kwargs = request.to_requests_kwargs()

        assert "timeout" in kwargs
        assert kwargs["timeout"] == 30.0

    def test_to_requests_kwargs_preserves_headers_and_params(self):
        """Test headers and params are preserved"""
        request = Request(
            method="GET",
            url="http://test.com",
            headers={"User-Agent": "test"},
            params={"q": "query", "page": 1},
        )
        kwargs = request.to_requests_kwargs()

        assert kwargs["headers"] == {"User-Agent": "test"}
        assert kwargs["params"] == {"q": "query", "page": 1}


class TestResponse:
    """Test Response model"""

    @pytest.fixture
    def mock_requests_response(self):
        """Create a mock requests.Response"""
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.headers = {"Content-Type": "application/json"}
        mock_resp.content = b'{"key": "value"}'
        mock_resp.text = '{"key": "value"}'
        mock_resp.url = "http://test.com/path"
        mock_resp.elapsed = timedelta(milliseconds=150)
        mock_resp.json.return_value = {"key": "value"}
        return mock_resp

    def test_from_requests_response(self, mock_requests_response):
        """Test creating Response from requests.Response"""
        response = Response.from_requests_response(mock_requests_response)

        assert response.status_code == 200
        assert response.headers == {"Content-Type": "application/json"}
        assert response.content == b'{"key": "value"}'
        assert response.text == '{"key": "value"}'
        assert response.url == "http://test.com/path"
        assert response.elapsed_ms == 150.0  # 150 milliseconds
        assert response._raw_response == mock_requests_response

    def test_json_method(self, mock_requests_response):
        """Test json() method delegates to raw response"""
        response = Response.from_requests_response(mock_requests_response)
        result = response.json()

        assert result == {"key": "value"}
        mock_requests_response.json.assert_called_once()

    def test_is_success_with_200(self):
        """Test is_success returns True for 200"""
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.headers = {}
        mock_resp.content = b""
        mock_resp.text = ""
        mock_resp.url = "http://test.com"
        mock_resp.elapsed = timedelta(milliseconds=100)

        response = Response.from_requests_response(mock_resp)
        assert response.is_success() is True

    def test_is_success_with_201(self):
        """Test is_success returns True for 201"""
        mock_resp = Mock()
        mock_resp.status_code = 201
        mock_resp.headers = {}
        mock_resp.content = b""
        mock_resp.text = ""
        mock_resp.url = "http://test.com"
        mock_resp.elapsed = timedelta(milliseconds=100)

        response = Response.from_requests_response(mock_resp)
        assert response.is_success() is True

    def test_is_success_with_204(self):
        """Test is_success returns True for 204"""
        mock_resp = Mock()
        mock_resp.status_code = 204
        mock_resp.headers = {}
        mock_resp.content = b""
        mock_resp.text = ""
        mock_resp.url = "http://test.com"
        mock_resp.elapsed = timedelta(milliseconds=100)

        response = Response.from_requests_response(mock_resp)
        assert response.is_success() is True

    def test_is_success_false_with_404(self):
        """Test is_success returns False for 404"""
        mock_resp = Mock()
        mock_resp.status_code = 404
        mock_resp.headers = {}
        mock_resp.content = b""
        mock_resp.text = ""
        mock_resp.url = "http://test.com"
        mock_resp.elapsed = timedelta(milliseconds=100)

        response = Response.from_requests_response(mock_resp)
        assert response.is_success() is False

    def test_is_success_false_with_500(self):
        """Test is_success returns False for 500"""
        mock_resp = Mock()
        mock_resp.status_code = 500
        mock_resp.headers = {}
        mock_resp.content = b""
        mock_resp.text = ""
        mock_resp.url = "http://test.com"
        mock_resp.elapsed = timedelta(milliseconds=100)

        response = Response.from_requests_response(mock_resp)
        assert response.is_success() is False

    def test_is_error_true_with_400(self):
        """Test is_error returns True for 400"""
        mock_resp = Mock()
        mock_resp.status_code = 400
        mock_resp.headers = {}
        mock_resp.content = b""
        mock_resp.text = ""
        mock_resp.url = "http://test.com"
        mock_resp.elapsed = timedelta(milliseconds=100)

        response = Response.from_requests_response(mock_resp)
        assert response.is_error() is True

    def test_is_error_true_with_404(self):
        """Test is_error returns True for 404"""
        mock_resp = Mock()
        mock_resp.status_code = 404
        mock_resp.headers = {}
        mock_resp.content = b""
        mock_resp.text = ""
        mock_resp.url = "http://test.com"
        mock_resp.elapsed = timedelta(milliseconds=100)

        response = Response.from_requests_response(mock_resp)
        assert response.is_error() is True

    def test_is_error_true_with_500(self):
        """Test is_error returns True for 500"""
        mock_resp = Mock()
        mock_resp.status_code = 500
        mock_resp.headers = {}
        mock_resp.content = b""
        mock_resp.text = ""
        mock_resp.url = "http://test.com"
        mock_resp.elapsed = timedelta(milliseconds=100)

        response = Response.from_requests_response(mock_resp)
        assert response.is_error() is True

    def test_is_error_false_with_200(self):
        """Test is_error returns False for 200"""
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.headers = {}
        mock_resp.content = b""
        mock_resp.text = ""
        mock_resp.url = "http://test.com"
        mock_resp.elapsed = timedelta(milliseconds=100)

        response = Response.from_requests_response(mock_resp)
        assert response.is_error() is False

    def test_is_error_false_with_301(self):
        """Test is_error returns False for 301 (redirect)"""
        mock_resp = Mock()
        mock_resp.status_code = 301
        mock_resp.headers = {}
        mock_resp.content = b""
        mock_resp.text = ""
        mock_resp.url = "http://test.com"
        mock_resp.elapsed = timedelta(milliseconds=100)

        response = Response.from_requests_response(mock_resp)
        assert response.is_error() is False

    def test_elapsed_ms_conversion(self):
        """Test elapsed time is correctly converted to milliseconds"""
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.headers = {}
        mock_resp.content = b""
        mock_resp.text = ""
        mock_resp.url = "http://test.com"
        mock_resp.elapsed = timedelta(seconds=1, milliseconds=500)  # 1.5 seconds

        response = Response.from_requests_response(mock_resp)
        assert response.elapsed_ms == 1500.0
