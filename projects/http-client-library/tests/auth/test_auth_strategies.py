"""
Tests for authentication strategies.

Pattern: Strategy (testing)
"""

import base64

import pytest

from http_client.auth.api_key import APIKeyAuth, header_api_key, query_api_key
from http_client.auth.base import AuthStrategy
from http_client.auth.basic import BasicAuth
from http_client.auth.bearer import BearerTokenAuth
from http_client.models import Request


class TestBearerTokenAuth:
    """Test BearerTokenAuth strategy"""

    def test_initialization(self):
        """Test bearer auth initializes correctly"""
        auth = BearerTokenAuth("test_token_123")
        assert auth.token == "test_token_123"

    def test_initialization_with_empty_token_raises_error(self):
        """Test that empty token raises ValueError"""
        with pytest.raises(ValueError):
            BearerTokenAuth("")

    def test_apply_adds_authorization_header(self):
        """Test that apply() adds Bearer token to Authorization header"""
        auth = BearerTokenAuth("secret_token")
        request = Request(method="GET", url="http://test.com")

        result = auth.apply(request)

        assert "Authorization" in result.headers
        assert result.headers["Authorization"] == "Bearer secret_token"

    def test_apply_returns_request(self):
        """Test that apply() returns the request"""
        auth = BearerTokenAuth("token")
        request = Request(method="GET", url="http://test.com")

        result = auth.apply(request)

        assert result is request

    def test_apply_with_existing_headers(self):
        """Test that apply() preserves existing headers"""
        auth = BearerTokenAuth("token")
        request = Request(
            method="GET", url="http://test.com", headers={"Content-Type": "application/json"}
        )

        result = auth.apply(request)

        assert result.headers["Content-Type"] == "application/json"
        assert result.headers["Authorization"] == "Bearer token"

    def test_apply_overwrites_existing_authorization(self):
        """Test that apply() overwrites existing Authorization header"""
        auth = BearerTokenAuth("new_token")
        request = Request(
            method="GET", url="http://test.com", headers={"Authorization": "Bearer old_token"}
        )

        result = auth.apply(request)

        assert result.headers["Authorization"] == "Bearer new_token"

    def test_repr_hides_token(self):
        """Test that __repr__ doesn't expose full token"""
        auth = BearerTokenAuth("secret_long_token_123")
        repr_str = repr(auth)

        assert "secr..." in repr_str
        assert "secret_long_token_123" not in repr_str

    def test_is_auth_strategy(self):
        """Test that BearerTokenAuth is an AuthStrategy"""
        auth = BearerTokenAuth("token")
        assert isinstance(auth, AuthStrategy)


class TestBasicAuth:
    """Test BasicAuth strategy"""

    def test_initialization(self):
        """Test basic auth initializes correctly"""
        auth = BasicAuth("user", "pass")
        assert auth.username == "user"
        assert auth.password == "pass"

    def test_initialization_with_empty_username_raises_error(self):
        """Test that empty username raises ValueError"""
        with pytest.raises(ValueError):
            BasicAuth("", "pass")

    def test_initialization_with_empty_password_allowed(self):
        """Test that empty password is allowed"""
        auth = BasicAuth("user", "")
        assert auth.password == ""

    def test_apply_adds_authorization_header(self):
        """Test that apply() adds Basic auth header"""
        auth = BasicAuth("user", "pass")
        request = Request(method="GET", url="http://test.com")

        result = auth.apply(request)

        assert "Authorization" in result.headers
        assert result.headers["Authorization"].startswith("Basic ")

    def test_apply_encodes_credentials_correctly(self):
        """Test that credentials are base64 encoded correctly"""
        auth = BasicAuth("testuser", "testpass")
        request = Request(method="GET", url="http://test.com")

        result = auth.apply(request)

        # Decode and verify
        auth_header = result.headers["Authorization"]
        encoded_part = auth_header.replace("Basic ", "")
        decoded = base64.b64decode(encoded_part).decode("utf-8")

        assert decoded == "testuser:testpass"

    def test_apply_with_special_characters(self):
        """Test encoding with special characters in password"""
        auth = BasicAuth("user", "p@ss:w0rd!")
        request = Request(method="GET", url="http://test.com")

        result = auth.apply(request)

        auth_header = result.headers["Authorization"]
        encoded_part = auth_header.replace("Basic ", "")
        decoded = base64.b64decode(encoded_part).decode("utf-8")

        assert decoded == "user:p@ss:w0rd!"

    def test_apply_returns_request(self):
        """Test that apply() returns the request"""
        auth = BasicAuth("user", "pass")
        request = Request(method="GET", url="http://test.com")

        result = auth.apply(request)

        assert result is request

    def test_repr_hides_password(self):
        """Test that __repr__ doesn't expose password"""
        auth = BasicAuth("john", "secret123")
        repr_str = repr(auth)

        assert "john" in repr_str
        assert "***" in repr_str
        assert "secret123" not in repr_str

    def test_is_auth_strategy(self):
        """Test that BasicAuth is an AuthStrategy"""
        auth = BasicAuth("user", "pass")
        assert isinstance(auth, AuthStrategy)


class TestAPIKeyAuth:
    """Test APIKeyAuth strategy"""

    def test_initialization_with_header(self):
        """Test API key auth initializes for header location"""
        auth = APIKeyAuth("key123", location="header", param_name="X-API-Key")

        assert auth.api_key == "key123"
        assert auth.location == "header"
        assert auth.param_name == "X-API-Key"

    def test_initialization_with_query(self):
        """Test API key auth initializes for query location"""
        auth = APIKeyAuth("key123", location="query", param_name="api_key")

        assert auth.location == "query"
        assert auth.param_name == "api_key"

    def test_initialization_with_invalid_location_raises_error(self):
        """Test that invalid location raises ValueError"""
        with pytest.raises(ValueError):
            APIKeyAuth("key123", location="invalid")

    def test_initialization_with_empty_key_raises_error(self):
        """Test that empty API key raises ValueError"""
        with pytest.raises(ValueError):
            APIKeyAuth("")

    def test_apply_adds_to_header(self):
        """Test that apply() adds API key to header when location=header"""
        auth = APIKeyAuth("secret_key", location="header", param_name="X-API-Key")
        request = Request(method="GET", url="http://test.com")

        result = auth.apply(request)

        assert result.headers["X-API-Key"] == "secret_key"

    def test_apply_adds_to_query_params(self):
        """Test that apply() adds API key to query params when location=query"""
        auth = APIKeyAuth("secret_key", location="query", param_name="api_key")
        request = Request(method="GET", url="http://test.com")

        result = auth.apply(request)

        assert result.params["api_key"] == "secret_key"

    def test_apply_preserves_existing_headers(self):
        """Test that apply() preserves existing headers"""
        auth = APIKeyAuth("key", location="header", param_name="X-API-Key")
        request = Request(
            method="GET", url="http://test.com", headers={"Content-Type": "application/json"}
        )

        result = auth.apply(request)

        assert result.headers["Content-Type"] == "application/json"
        assert result.headers["X-API-Key"] == "key"

    def test_apply_preserves_existing_params(self):
        """Test that apply() preserves existing query params"""
        auth = APIKeyAuth("key", location="query", param_name="api_key")
        request = Request(method="GET", url="http://test.com", params={"page": 1})

        result = auth.apply(request)

        assert result.params["page"] == 1
        assert result.params["api_key"] == "key"

    def test_apply_returns_request(self):
        """Test that apply() returns the request"""
        auth = APIKeyAuth("key", location="header")
        request = Request(method="GET", url="http://test.com")

        result = auth.apply(request)

        assert result is request

    def test_default_param_name(self):
        """Test default parameter name is X-API-Key"""
        auth = APIKeyAuth("key123")
        assert auth.param_name == "X-API-Key"

    def test_default_location(self):
        """Test default location is header"""
        auth = APIKeyAuth("key123")
        assert auth.location == "header"

    def test_repr_hides_key(self):
        """Test that __repr__ doesn't expose full API key"""
        auth = APIKeyAuth("secret_long_key_123", location="header")
        repr_str = repr(auth)

        assert "secr..." in repr_str
        assert "secret_long_key_123" not in repr_str

    def test_is_auth_strategy(self):
        """Test that APIKeyAuth is an AuthStrategy"""
        auth = APIKeyAuth("key")
        assert isinstance(auth, AuthStrategy)


class TestAPIKeyHelpers:
    """Test API key helper functions"""

    def test_header_api_key_creates_header_auth(self):
        """Test header_api_key() helper creates header-based auth"""
        auth = header_api_key("key123", "X-Custom-Key")

        assert auth.location == "header"
        assert auth.param_name == "X-Custom-Key"
        assert auth.api_key == "key123"

    def test_header_api_key_default_name(self):
        """Test header_api_key() uses default header name"""
        auth = header_api_key("key123")
        assert auth.param_name == "X-API-Key"

    def test_query_api_key_creates_query_auth(self):
        """Test query_api_key() helper creates query-based auth"""
        auth = query_api_key("key123", "token")

        assert auth.location == "query"
        assert auth.param_name == "token"
        assert auth.api_key == "key123"

    def test_query_api_key_default_name(self):
        """Test query_api_key() uses default param name"""
        auth = query_api_key("key123")
        assert auth.param_name == "api_key"
