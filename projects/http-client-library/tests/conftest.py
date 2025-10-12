"""
Pytest configuration and shared fixtures.

This file provides common fixtures used across all tests.
"""

from datetime import timedelta
from unittest.mock import Mock

import pytest


@pytest.fixture
def mock_requests_response():
    """
    Create a mock requests.Response object.

    Useful for testing without making real HTTP calls.
    """
    mock_resp = Mock()
    mock_resp.status_code = 200
    mock_resp.headers = {"Content-Type": "application/json"}
    mock_resp.content = b'{"message": "success"}'
    mock_resp.text = '{"message": "success"}'
    mock_resp.url = "http://test.com/endpoint"
    mock_resp.elapsed = timedelta(milliseconds=100)
    mock_resp.json.return_value = {"message": "success"}
    return mock_resp


@pytest.fixture
def sample_request():
    """Create a sample Request object for testing."""
    from http_client.models import Request

    return Request(
        method="GET",
        url="http://test.com/path",
        headers={"User-Agent": "test"},
        params={"q": "test"},
        timeout=30.0,
    )


@pytest.fixture
def sample_response(mock_requests_response):
    """Create a sample Response object for testing."""
    from http_client.models import Response

    return Response.from_requests_response(mock_requests_response)


# Pytest markers for organizing tests
def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line("markers", "integration: mark test as integration test (skipped in CI)")
    config.addinivalue_line("markers", "slow: mark test as slow running")
