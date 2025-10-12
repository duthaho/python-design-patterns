"""
Request and Response models.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, Optional

import requests


@dataclass
class Request:
    """
    Wrapper around request parameters.

    This abstraction allows middleware to modify requests
    without depending on the underlying HTTP library.
    """

    method: str
    url: str
    headers: Dict[str, str] = field(default_factory=dict)
    params: Dict[str, Any] = field(default_factory=dict)
    data: Optional[Any] = None
    json: Optional[Dict] = None
    timeout: Optional[float] = None

    def to_requests_kwargs(self) -> Dict[str, Any]:
        """Convert to kwargs dict for requests library."""
        kwargs = {
            "method": self.method,
            "url": self.url,
            "headers": self.headers,
            "params": self.params,
            "timeout": self.timeout,
        }
        if self.json is not None:
            kwargs["json"] = self.json
        elif self.data is not None:
            kwargs["data"] = self.data
        # Filter out None values
        return {k: v for k, v in kwargs.items() if v is not None}


@dataclass
class Response:
    """
    Wrapper around HTTP response.

    Provides a clean interface for middleware to inspect/modify responses.
    """

    status_code: int
    headers: Dict[str, str]
    content: bytes
    text: str
    url: str
    elapsed_ms: float
    _raw_response: requests.Response = field(repr=False)

    @classmethod
    def from_requests_response(cls, response: requests.Response) -> "Response":
        """Factory method to create Response from requests.Response."""
        return cls(
            status_code=response.status_code,
            headers=dict(response.headers),
            content=response.content,
            text=response.text,
            url=response.url,
            elapsed_ms=response.elapsed.total_seconds() * 1000,
            _raw_response=response,
        )

    def json(self) -> Dict:
        """Parse JSON response body."""
        return self._raw_response.json()

    def is_success(self) -> bool:
        """Check if response indicates success (2xx status code)."""
        return 200 <= self.status_code < 300

    def is_error(self) -> bool:
        """Check if response indicates error (4xx or 5xx)"""
        return 400 <= self.status_code < 600
