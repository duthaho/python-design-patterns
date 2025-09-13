import json
import logging
import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, BinaryIO, Callable, Dict, List, Optional, Union
from urllib.parse import urlencode

logger = logging.getLogger(__name__)


# ============================================================================
# ENUMS AND BASIC TYPES
# ============================================================================


class HTTPMethod(Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"


class AuthType(Enum):
    NONE = "none"
    BASIC = "basic"
    BEARER = "bearer"
    API_KEY = "api_key"
    CUSTOM = "custom"


class ContentType(Enum):
    JSON = "application/json"
    XML = "application/xml"
    FORM_DATA = "application/x-www-form-urlencoded"
    MULTIPART = "multipart/form-data"
    TEXT_PLAIN = "text/plain"
    OCTET_STREAM = "application/octet-stream"


class RetryStrategy(Enum):
    NONE = "none"
    LINEAR = "linear"
    EXPONENTIAL = "exponential"
    FIXED = "fixed"


class CacheStrategy(Enum):
    NONE = "none"
    MEMORY = "memory"
    DISK = "disk"
    REDIS = "redis"


# ============================================================================
# DATA CLASSES FOR REQUEST COMPONENTS
# ============================================================================


@dataclass(frozen=True)
class Authentication:
    """Authentication configuration"""

    auth_type: AuthType
    username: str = ""
    password: str = ""
    token: str = ""
    api_key: str = ""
    api_key_header: str = "X-API-Key"
    custom_headers: Dict[str, str] = field(default_factory=dict)

    def validate(self) -> List[str]:
        """Validate authentication configuration"""
        # TODO: Implement validation logic
        # - Check required fields based on auth_type
        # - Validate token format for Bearer auth
        # - Check API key configuration
        errors = []
        if self.auth_type == AuthType.BASIC:
            if not self.username or not self.password:
                errors.append("Basic auth requires username and password")
        elif self.auth_type == AuthType.BEARER:
            if not self.token:
                errors.append("Bearer auth requires token")
        elif self.auth_type == AuthType.API_KEY:
            if not self.api_key:
                errors.append("API key auth requires api_key")
        elif self.auth_type == AuthType.CUSTOM:
            if not self.custom_headers:
                errors.append("Custom auth requires custom_headers")
        return errors


@dataclass(frozen=True)
class RetryPolicy:
    """Retry policy configuration"""

    strategy: RetryStrategy
    max_attempts: int = 3
    base_delay_seconds: float = 1.0
    max_delay_seconds: float = 60.0
    backoff_multiplier: float = 2.0
    retry_on_status_codes: tuple[int, ...] = field(
        default_factory=lambda: (500, 502, 503, 504)
    )

    def validate(self) -> List[str]:
        """Validate retry policy"""
        # TODO: Implement validation
        # - Check max_attempts > 0
        # - Validate delay values
        # - Check backoff_multiplier > 1 for exponential strategy
        errors = []
        if self.max_attempts < 1:
            errors.append("max_attempts must be at least 1")
        if self.base_delay_seconds < 0:
            errors.append("base_delay_seconds must be non-negative")
        if self.max_delay_seconds < self.base_delay_seconds:
            errors.append("max_delay_seconds must be >= base_delay_seconds")
        if self.strategy == RetryStrategy.EXPONENTIAL and self.backoff_multiplier <= 1:
            errors.append("backoff_multiplier must be > 1 for exponential strategy")
        return errors

    def get_next_delay(self, attempt: int) -> float:
        """Calculate delay before next retry based on strategy and attempt number"""
        if self.strategy == RetryStrategy.NONE or attempt >= self.max_attempts:
            return 0.0
        if self.strategy == RetryStrategy.LINEAR:
            delay = self.base_delay_seconds * attempt
        elif self.strategy == RetryStrategy.EXPONENTIAL:
            delay = self.base_delay_seconds * (self.backoff_multiplier ** (attempt - 1))
        elif self.strategy == RetryStrategy.FIXED:
            delay = self.base_delay_seconds
        else:
            delay = 0.0
        return min(delay, self.max_delay_seconds)


@dataclass(frozen=True)
class TimeoutConfig:
    """Timeout configuration"""

    connect_timeout_seconds: float = 30.0
    read_timeout_seconds: float = 30.0
    total_timeout_seconds: float = 60.0

    def validate(self) -> List[str]:
        """Validate timeout configuration"""
        # TODO: Implement validation
        # - All timeouts must be positive
        # - total_timeout should be >= connect_timeout + read_timeout
        errors = []
        if self.connect_timeout_seconds <= 0:
            errors.append("connect_timeout_seconds must be positive")
        if self.read_timeout_seconds <= 0:
            errors.append("read_timeout_seconds must be positive")
        if self.total_timeout_seconds < (
            self.connect_timeout_seconds + self.read_timeout_seconds
        ):
            errors.append(
                "total_timeout_seconds must be >= connect_timeout_seconds + read_timeout_seconds"
            )
        return errors


@dataclass(frozen=True)
class CacheConfig:
    """Cache configuration"""

    strategy: CacheStrategy
    ttl_seconds: int = 300
    cache_key_prefix: str = "http_cache"
    cache_on_status_codes: tuple[int, ...] = field(default_factory=lambda: (200,))

    def validate(self) -> List[str]:
        """Validate cache configuration"""
        # TODO: Implement validation
        errors = []
        if self.strategy != CacheStrategy.NONE and self.ttl_seconds <= 0:
            errors.append("ttl_seconds must be positive for caching strategies")
        return errors if self.strategy != CacheStrategy.NONE else []


@dataclass(frozen=True)
class CircuitBreakerConfig:
    """Circuit breaker configuration"""

    enabled: bool = False
    failure_threshold: int = 5
    timeout_seconds: float = 60.0
    half_open_max_calls: int = 3

    def validate(self) -> List[str]:
        """Validate circuit breaker configuration"""
        # TODO: Implement validation
        errors = []
        if self.enabled:
            if self.failure_threshold < 1:
                errors.append("failure_threshold must be at least 1")
            if self.timeout_seconds <= 0:
                errors.append("timeout_seconds must be positive")
            if self.half_open_max_calls < 1:
                errors.append("half_open_max_calls must be at least 1")
        return errors if self.enabled else []


@dataclass
class FileUpload:
    """File upload specification"""

    field_name: str
    filename: str
    content: Union[bytes, BinaryIO]
    content_type: str = "application/octet-stream"


@dataclass(frozen=True)
class HTTPRequest:
    """Final immutable HTTP request configuration"""

    method: HTTPMethod
    url: str
    headers: Dict[str, str] = field(default_factory=dict)
    query_params: Dict[str, str] = field(default_factory=dict)
    body: Optional[Union[str, bytes, Dict[str, Any]]] = None
    files: tuple[FileUpload, ...] = field(default_factory=tuple)
    authentication: Optional[Authentication] = None
    retry_policy: RetryPolicy = field(default_factory=RetryPolicy)
    timeout_config: TimeoutConfig = field(default_factory=TimeoutConfig)
    cache_config: CacheConfig = field(default_factory=CacheConfig)
    circuit_breaker: CircuitBreakerConfig = field(default_factory=CircuitBreakerConfig)

    def validate_complete_request(self) -> List[str]:
        """Perform final request validation"""
        # TODO: Implement comprehensive validation
        # - URL format validation
        # - Method-specific validations (GET shouldn't have body, etc.)
        # - Content-Type header consistency with body type
        # - File upload validations
        # - Cross-component validations
        errors = []
        if not self.url.startswith(("http://", "https://")):
            errors.append("URL must start with http:// or https://")
        if (
            self.method in {HTTPMethod.GET, HTTPMethod.DELETE, HTTPMethod.HEAD}
            and self.body is not None
        ):
            errors.append(f"{self.method.value} requests should not have a body")
        if self.body is not None and isinstance(self.body, dict):
            content_type = self.headers.get("Content-Type", "")
            if content_type != ContentType.JSON.value:
                errors.append("JSON body requires Content-Type to be application/json")
        if self.files and self.method not in {
            HTTPMethod.POST,
            HTTPMethod.PUT,
            HTTPMethod.PATCH,
        }:
            errors.append(
                f"File uploads are only supported with POST, PUT, or PATCH methods"
            )
        return errors

    def to_dict(self) -> Dict[str, Any]:
        """Convert request to dictionary representation"""
        # TODO: Implement serialization for logging/debugging
        return {
            "method": self.method.value,
            "url": self.url,
            "headers": self.headers,
            "query_params": self.query_params,
            "body": self.body if not isinstance(self.body, bytes) else "<binary data>",
            "files": [f.filename for f in self.files],
            "authentication": (
                self.authentication.auth_type.value if self.authentication else "none"
            ),
            "retry_policy": {
                "strategy": self.retry_policy.strategy.value,
                "max_attempts": self.retry_policy.max_attempts,
            },
            "timeout_config": {
                "connect_timeout_seconds": self.timeout_config.connect_timeout_seconds,
                "read_timeout_seconds": self.timeout_config.read_timeout_seconds,
                "total_timeout_seconds": self.timeout_config.total_timeout_seconds,
            },
            "cache_config": {
                "strategy": self.cache_config.strategy.value,
                "ttl_seconds": self.cache_config.ttl_seconds,
            },
            "circuit_breaker": {
                "enabled": self.circuit_breaker.enabled,
                "failure_threshold": self.circuit_breaker.failure_threshold,
            },
        }


# ============================================================================
# INTERCEPTOR FRAMEWORK
# ============================================================================


class RequestInterceptor(ABC):
    """Abstract base class for request interceptors"""

    @abstractmethod
    def intercept(self, request: HTTPRequest) -> HTTPRequest:
        """Modify request before execution"""
        pass


class ResponseInterceptor(ABC):
    """Abstract base class for response interceptors"""

    @abstractmethod
    def intercept(self, request: HTTPRequest, response: Any) -> Any:
        """Modify response after execution"""
        pass


class LoggingInterceptor(RequestInterceptor):
    """Logs request details"""

    def __init__(self, log_level: str = "INFO"):
        self.log_level = log_level

    def intercept(self, request: HTTPRequest) -> HTTPRequest:
        # TODO: Implement request logging
        # - Log method, URL, headers (sensitive data masked)
        # - Include timestamp, correlation ID
        # - Support different log levels
        logger_method = getattr(logger, self.log_level.lower(), logger.info)
        logger_method(f"HTTP Request: {request.method.value} {request.url}")
        if request.headers:
            masked_headers = {
                k: (v if k.lower() not in {"authorization", "api_key"} else "****")
                for k, v in request.headers.items()
            }
            logger_method(f"Headers: {json.dumps(masked_headers)}")
        if request.query_params:
            logger_method(f"Query Params: {urlencode(request.query_params)}")
        if request.body:
            if isinstance(request.body, bytes):
                logger_method("Body: <binary data>")
            else:
                logger_method(f"Body: {json.dumps(request.body)}")
        if request.files:
            logger_method(f"Files: {[f.filename for f in request.files]}")
        return request


class RateLimitInterceptor(RequestInterceptor):
    """Enforces rate limiting"""

    def __init__(self, requests_per_second: float = 10.0):
        self.requests_per_second = requests_per_second
        # TODO: Add rate limiting state tracking
        self.last_request_time = 0.0

    def intercept(self, request: HTTPRequest) -> HTTPRequest:
        # TODO: Implement rate limiting logic
        # - Track request timestamps
        # - Sleep if rate limit exceeded
        # - Support different rate limiting strategies
        logger.debug(f"Rate limiting at {self.requests_per_second} RPS")
        current_time = time.time()
        elapsed = current_time - self.last_request_time
        min_interval = 1.0 / self.requests_per_second
        if elapsed < min_interval:
            sleep_time = min_interval - elapsed
            logger.debug(f"Sleeping for {sleep_time:.3f} seconds to enforce rate limit")
            time.sleep(sleep_time)
        self.last_request_time = time.time()
        return request


class RequestSigningInterceptor(RequestInterceptor):
    """Signs requests for secure APIs"""

    def __init__(self, secret_key: str, algorithm: str = "HMAC-SHA256"):
        self.secret_key = secret_key
        self.algorithm = algorithm

    def intercept(self, request: HTTPRequest) -> HTTPRequest:
        # TODO: Implement request signing
        # - Generate signature based on request components
        # - Add signature headers
        # - Support different signing algorithms
        logger.debug(f"Signing request with {self.algorithm}")
        if not self.secret_key:
            logger.warning("No secret key provided for signing")
            return request
        if "Authorization" in request.headers:
            logger.warning("Authorization header already present, skipping signing")
            return request
        signature = f"signed-with-{self.algorithm}"
        signed_headers = dict(request.headers)
        signed_headers["Authorization"] = signature
        return HTTPRequest(
            method=request.method,
            url=request.url,
            headers=signed_headers,
            query_params=request.query_params,
            body=request.body,
            files=request.files,
            authentication=request.authentication,
            retry_policy=request.retry_policy,
            timeout_config=request.timeout_config,
            cache_config=request.cache_config,
            circuit_breaker=request.circuit_breaker,
        )


# ============================================================================
# BUILDER STATES AND VALIDATION
# ============================================================================


class BuilderState(Enum):
    """HTTP Request Builder states"""

    INITIAL = "initial"
    URL_SET = "url_set"
    METHOD_SET = "method_set"
    HEADERS_CONFIGURED = "headers_configured"
    BODY_CONFIGURED = "body_configured"
    AUTH_CONFIGURED = "auth_configured"
    POLICIES_CONFIGURED = "policies_configured"
    READY_TO_BUILD = "ready_to_build"


class RequestValidationRule(ABC):
    """Abstract base for request validation rules"""

    @abstractmethod
    def validate(self, builder: "HTTPRequestBuilder") -> List[str]:
        pass

    @abstractmethod
    def applies_to_state(self, state: BuilderState) -> bool:
        pass


class MethodBodyValidationRule(RequestValidationRule):
    """Validates method and body compatibility"""

    def validate(self, builder: "HTTPRequestBuilder") -> List[str]:
        # TODO: Implement validation
        # - GET, DELETE, HEAD shouldn't have body
        # - POST, PUT, PATCH should have body for most APIs
        # - OPTIONS can have body in some cases
        errors = []
        if (
            builder._method in {HTTPMethod.GET, HTTPMethod.DELETE, HTTPMethod.HEAD}
            and builder._body is not None
        ):
            errors.append(f"{builder._method.value} requests should not have a body")
        if (
            builder._method in {HTTPMethod.POST, HTTPMethod.PUT, HTTPMethod.PATCH}
            and builder._body is None
            and not builder._files
        ):
            errors.append(f"{builder._method.value} requests typically require a body")
        return errors

    def applies_to_state(self, state: BuilderState) -> bool:
        # TODO: Return True when both method and body are potentially set
        return state in {BuilderState.BODY_CONFIGURED, BuilderState.READY_TO_BUILD}


class ContentTypeValidationRule(RequestValidationRule):
    """Validates Content-Type header matches body type"""

    def validate(self, builder: "HTTPRequestBuilder") -> List[str]:
        # TODO: Implement validation
        # - JSON body should have application/json Content-Type
        # - Form data should have appropriate Content-Type
        # - File uploads should have multipart/form-data
        errors = []
        if builder._body is not None:
            content_type = builder._headers.get("Content-Type", "")
            if (
                isinstance(builder._body, dict)
                and content_type != ContentType.JSON.value
            ):
                errors.append("JSON body requires Content-Type to be application/json")
            if builder._files and content_type != ContentType.MULTIPART.value:
                errors.append(
                    "File uploads require Content-Type to be multipart/form-data"
                )
        return errors if builder._body is not None else []

    def applies_to_state(self, state: BuilderState) -> bool:
        # TODO: Return True when headers and body are configured
        return state in {
            BuilderState.HEADERS_CONFIGURED,
            BuilderState.BODY_CONFIGURED,
            BuilderState.READY_TO_BUILD,
        }


class AuthenticationValidationRule(RequestValidationRule):
    """Validates authentication configuration"""

    def validate(self, builder: "HTTPRequestBuilder") -> List[str]:
        # TODO: Implement validation
        # - Check required fields are present for auth type
        # - Validate token formats
        # - Ensure no conflicting auth methods
        errors = []
        if builder._authentication:
            errors.extend(builder._authentication.validate())
        return errors

    def applies_to_state(self, state: BuilderState) -> bool:
        # TODO: Return True when auth is configured
        return state in {BuilderState.AUTH_CONFIGURED, BuilderState.READY_TO_BUILD}


# ============================================================================
# MAIN HTTP REQUEST BUILDER
# ============================================================================


class HTTPRequestBuilder:
    """
    Enterprise-grade HTTP Request Builder with advanced features
    """

    def __init__(self):
        # Builder state
        self._state: BuilderState = BuilderState.INITIAL

        # Request components
        self._method: Optional[HTTPMethod] = None
        self._url: str = ""
        self._headers: Dict[str, str] = {}
        self._query_params: Dict[str, str] = {}
        self._body: Optional[Union[str, bytes, Dict[str, Any]]] = None
        self._files: List[FileUpload] = []

        # Configuration components
        self._authentication: Optional[Authentication] = None
        self._retry_policy: RetryPolicy = RetryPolicy(RetryStrategy.NONE)
        self._timeout_config: TimeoutConfig = TimeoutConfig()
        self._cache_config: CacheConfig = CacheConfig(CacheStrategy.NONE)
        self._circuit_breaker: CircuitBreakerConfig = CircuitBreakerConfig()

        # Interceptors
        self._request_interceptors: List[RequestInterceptor] = []
        self._response_interceptors: List[ResponseInterceptor] = []

        # Validation rules
        self._validation_rules: List[RequestValidationRule] = [
            MethodBodyValidationRule(),
            ContentTypeValidationRule(),
            AuthenticationValidationRule(),
        ]

        # Operation history for advanced debugging
        self._operation_history: List[str] = []

    # ========================================================================
    # STATE MANAGEMENT
    # ========================================================================

    def _transition_to_state(self, new_state: BuilderState) -> None:
        """Transition to new state with validation"""
        # TODO: Implement state transition logic
        if self._validate_state_transition(self._state, new_state):
            self._state = new_state
            self._log_operation(f"Transitioned to state: {new_state.value}")
            self._run_validations()
        else:
            raise ValueError(
                f"Invalid state transition from {self._state} to {new_state}"
            )

    def _validate_state_transition(
        self, from_state: BuilderState, to_state: BuilderState
    ) -> bool:
        """Validate state transitions"""
        # TODO: Define valid transitions
        # INITIAL -> URL_SET -> METHOD_SET -> ... -> READY_TO_BUILD
        if from_state == to_state:
            return True

        valid_transitions = {
            BuilderState.INITIAL: [BuilderState.URL_SET],
            BuilderState.URL_SET: [BuilderState.METHOD_SET],
            BuilderState.METHOD_SET: [
                BuilderState.HEADERS_CONFIGURED,
                BuilderState.BODY_CONFIGURED,
                BuilderState.AUTH_CONFIGURED,
                BuilderState.POLICIES_CONFIGURED,
                BuilderState.READY_TO_BUILD,
            ],
            BuilderState.HEADERS_CONFIGURED: [
                BuilderState.BODY_CONFIGURED,
                BuilderState.AUTH_CONFIGURED,
                BuilderState.POLICIES_CONFIGURED,
                BuilderState.READY_TO_BUILD,
            ],
            BuilderState.BODY_CONFIGURED: [
                BuilderState.AUTH_CONFIGURED,
                BuilderState.POLICIES_CONFIGURED,
                BuilderState.READY_TO_BUILD,
            ],
            BuilderState.AUTH_CONFIGURED: [
                BuilderState.POLICIES_CONFIGURED,
                BuilderState.READY_TO_BUILD,
            ],
            BuilderState.POLICIES_CONFIGURED: [BuilderState.READY_TO_BUILD],
            BuilderState.READY_TO_BUILD: [],
        }
        return to_state in valid_transitions.get(from_state, [])

    def _run_validations(self) -> None:
        """Run applicable validation rules"""
        # TODO: Implement validation execution
        errors = []
        for rule in self._validation_rules:
            if rule.applies_to_state(self._state):
                errors.extend(rule.validate(self))
        if errors:
            raise ValueError("Validation errors: " + "; ".join(errors))

    def _log_operation(self, operation: str) -> None:
        """Log operation for debugging"""
        # TODO: Add operation to history with timestamp
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        self._operation_history.append(f"[{timestamp}] {operation}")

    # ========================================================================
    # BASIC REQUEST CONFIGURATION
    # ========================================================================

    def url(self, url: str) -> "HTTPRequestBuilder":
        """Set request URL - must be called first"""
        # TODO: Implement
        # - Validate URL format
        # - Extract and set base URL
        # - Handle URL templates/parameters
        # - Transition to URL_SET state
        if self._state != BuilderState.INITIAL:
            raise ValueError("URL can only be set in INITIAL state")
        if not url:
            raise ValueError("URL cannot be empty")
        self._url = url
        self._transition_to_state(BuilderState.URL_SET)
        return self

    def method(self, method: HTTPMethod) -> "HTTPRequestBuilder":
        """Set HTTP method"""
        # TODO: Implement
        # - Validate method is supported
        # - Transition to METHOD_SET state
        if self._state != BuilderState.URL_SET:
            raise ValueError("Method can only be set in URL_SET state")
        if not isinstance(method, HTTPMethod):
            raise ValueError("Invalid HTTP method")
        self._method = method
        self._transition_to_state(BuilderState.METHOD_SET)
        return self

    def get(self, url: str = None) -> "HTTPRequestBuilder":
        """Convenience method for GET requests"""
        # TODO: Implement as combination of url() and method()
        return self.url(url).method(HTTPMethod.GET)

    def post(self, url: str = None) -> "HTTPRequestBuilder":
        """Convenience method for POST requests"""
        # TODO: Implement
        return self.url(url).method(HTTPMethod.POST)

    def put(self, url: str = None) -> "HTTPRequestBuilder":
        """Convenience method for PUT requests"""
        # TODO: Implement
        return self.url(url).method(HTTPMethod.PUT)

    def delete(self, url: str = None) -> "HTTPRequestBuilder":
        """Convenience method for DELETE requests"""
        # TODO: Implement
        return self.url(url).method(HTTPMethod.DELETE)

    def patch(self, url: str = None) -> "HTTPRequestBuilder":
        """Convenience method for PATCH requests"""
        # TODO: Implement
        return self.url(url).method(HTTPMethod.PATCH)

    # ========================================================================
    # HEADERS AND PARAMETERS
    # ========================================================================

    def header(self, name: str, value: str) -> "HTTPRequestBuilder":
        """Add single header"""
        # TODO: Implement
        # - Validate header name/value
        # - Handle case sensitivity
        # - Transition to HEADERS_CONFIGURED if needed
        if self._state not in {
            BuilderState.METHOD_SET,
            BuilderState.HEADERS_CONFIGURED,
            BuilderState.BODY_CONFIGURED,
            BuilderState.AUTH_CONFIGURED,
            BuilderState.POLICIES_CONFIGURED,
        }:
            raise ValueError("Headers can only be set after method is configured")
        if not name or not value:
            raise ValueError("Header name and value cannot be empty")
        self._headers[name] = value
        if self._state == BuilderState.METHOD_SET:
            self._transition_to_state(BuilderState.HEADERS_CONFIGURED)
        return self

    def headers(self, headers: Dict[str, str]) -> "HTTPRequestBuilder":
        """Add multiple headers"""
        # TODO: Implement using header() method
        for name, value in headers.items():
            self.header(name, value)
        return self

    def content_type(self, content_type: ContentType) -> "HTTPRequestBuilder":
        """Set Content-Type header"""
        # TODO: Implement as specialized header method
        return self.header("Content-Type", content_type.value)

    def accept(self, accept: str) -> "HTTPRequestBuilder":
        """Set Accept header"""
        # TODO: Implement
        return self.header("Accept", accept)

    def user_agent(self, user_agent: str) -> "HTTPRequestBuilder":
        """Set User-Agent header"""
        # TODO: Implement
        return self.header("User-Agent", user_agent)

    def query_param(self, name: str, value: str) -> "HTTPRequestBuilder":
        """Add single query parameter"""
        # TODO: Implement
        # - Handle URL encoding
        # - Support array parameters
        if self._state not in {
            BuilderState.METHOD_SET,
            BuilderState.HEADERS_CONFIGURED,
            BuilderState.BODY_CONFIGURED,
            BuilderState.AUTH_CONFIGURED,
            BuilderState.POLICIES_CONFIGURED,
        }:
            raise ValueError(
                "Query parameters can only be set after method is configured"
            )
        if not name or not value:
            raise ValueError("Query parameter name and value cannot be empty")
        self._query_params[name] = value
        return self

    def query_params(self, params: Dict[str, str]) -> "HTTPRequestBuilder":
        """Add multiple query parameters"""
        # TODO: Implement
        for name, value in params.items():
            self.query_param(name, value)
        return self

    # ========================================================================
    # REQUEST BODY CONFIGURATION
    # ========================================================================

    def body_raw(self, body: Union[str, bytes]) -> "HTTPRequestBuilder":
        """Set raw request body"""
        # TODO: Implement
        # - Validate body based on method
        # - Transition to BODY_CONFIGURED state
        if self._state not in {
            BuilderState.METHOD_SET,
            BuilderState.HEADERS_CONFIGURED,
        }:
            raise ValueError("Body can only be set after method is configured")
        if not body:
            raise ValueError("Body cannot be empty")
        self._body = body
        if self._state in {BuilderState.METHOD_SET, BuilderState.HEADERS_CONFIGURED}:
            self._transition_to_state(BuilderState.BODY_CONFIGURED)
        return self

    def body_json(self, data: Dict[str, Any]) -> "HTTPRequestBuilder":
        """Set JSON request body"""
        # TODO: Implement
        # - Serialize to JSON
        # - Set appropriate Content-Type
        # - Handle serialization errors
        if self._state not in {
            BuilderState.METHOD_SET,
            BuilderState.HEADERS_CONFIGURED,
        }:
            raise ValueError("Body can only be set after method is configured")
        if not isinstance(data, dict):
            raise ValueError("JSON body must be a dictionary")
        try:
            self._body = json.dumps(data)
        except (TypeError, ValueError) as e:
            raise ValueError(f"Error serializing JSON body: {e}")
        self.content_type(ContentType.JSON)
        if self._state in {BuilderState.METHOD_SET, BuilderState.HEADERS_CONFIGURED}:
            self._transition_to_state(BuilderState.BODY_CONFIGURED)
        return self

    def body_form(self, data: Dict[str, str]) -> "HTTPRequestBuilder":
        """Set form-encoded request body"""
        # TODO: Implement
        # - URL encode form data
        # - Set application/x-www-form-urlencoded Content-Type
        if self._state not in {
            BuilderState.METHOD_SET,
            BuilderState.HEADERS_CONFIGURED,
            BuilderState.BODY_CONFIGURED,
        }:
            raise ValueError("Body can only be set after method is configured")
        if not isinstance(data, dict):
            raise ValueError("Form body must be a dictionary")
        self._body = urlencode(data)
        self.content_type(ContentType.FORM_DATA)
        if self._state in {BuilderState.METHOD_SET, BuilderState.HEADERS_CONFIGURED}:
            self._transition_to_state(BuilderState.BODY_CONFIGURED)
        return self

    def body_xml(self, xml_data: str) -> "HTTPRequestBuilder":
        """Set XML request body"""
        # TODO: Implement
        # - Validate XML format
        # - Set application/xml Content-Type
        if self._state not in {
            BuilderState.METHOD_SET,
            BuilderState.HEADERS_CONFIGURED,
        }:
            raise ValueError("Body can only be set after method is configured")
        if not isinstance(xml_data, str):
            raise ValueError("XML body must be a string")
        self._body = xml_data
        self.content_type(ContentType.XML)
        if self._state in {BuilderState.METHOD_SET, BuilderState.HEADERS_CONFIGURED}:
            self._transition_to_state(BuilderState.BODY_CONFIGURED)
        return self

    # ========================================================================
    # FILE UPLOAD SUPPORT
    # ========================================================================

    def file(
        self,
        field_name: str,
        filename: str,
        content: Union[bytes, BinaryIO],
        content_type: str = None,
    ) -> "HTTPRequestBuilder":
        """Add file upload"""
        # TODO: Implement
        # - Create FileUpload object
        # - Set multipart/form-data Content-Type
        # - Handle content type detection
        if self._state not in {
            BuilderState.METHOD_SET,
            BuilderState.HEADERS_CONFIGURED,
        }:
            raise ValueError("Files can only be added after method is configured")
        if not field_name or not filename or not content:
            raise ValueError("field_name, filename, and content cannot be empty")
        file_upload = FileUpload(
            field_name=field_name,
            filename=filename,
            content=content,
            content_type=content_type or "application/octet-stream",
        )
        self._files.append(file_upload)
        self.content_type(ContentType.MULTIPART)
        if self._state in {BuilderState.METHOD_SET, BuilderState.HEADERS_CONFIGURED}:
            self._transition_to_state(BuilderState.BODY_CONFIGURED)
        return self

    def files(self, files: List[FileUpload]) -> "HTTPRequestBuilder":
        """Add multiple file uploads"""
        # TODO: Implement
        for file in files:
            self.file(file.field_name, file.filename, file.content, file.content_type)
        return self

    # ========================================================================
    # AUTHENTICATION
    # ========================================================================

    def auth_basic(self, username: str, password: str) -> "HTTPRequestBuilder":
        """Set basic authentication"""
        # TODO: Implement
        # - Create Authentication object
        # - Transition to AUTH_CONFIGURED state
        if self._state not in {
            BuilderState.METHOD_SET,
            BuilderState.HEADERS_CONFIGURED,
            BuilderState.BODY_CONFIGURED,
        }:
            raise ValueError(
                "Authentication can only be set after method is configured"
            )
        if not username or not password:
            raise ValueError("Username and password cannot be empty")
        self._authentication = Authentication(
            auth_type=AuthType.BASIC, username=username, password=password
        )
        self._transition_to_state(BuilderState.AUTH_CONFIGURED)
        return self

    def auth_bearer(self, token: str) -> "HTTPRequestBuilder":
        """Set bearer token authentication"""
        # TODO: Implement
        if self._state not in {
            BuilderState.METHOD_SET,
            BuilderState.HEADERS_CONFIGURED,
            BuilderState.BODY_CONFIGURED,
        }:
            raise ValueError(
                "Authentication can only be set after method is configured"
            )
        if not token:
            raise ValueError("Token cannot be empty")
        self._authentication = Authentication(auth_type=AuthType.BEARER, token=token)
        self._transition_to_state(BuilderState.AUTH_CONFIGURED)
        return self

    def auth_api_key(
        self, api_key: str, header_name: str = "X-API-Key"
    ) -> "HTTPRequestBuilder":
        """Set API key authentication"""
        # TODO: Implement
        if self._state not in {
            BuilderState.METHOD_SET,
            BuilderState.HEADERS_CONFIGURED,
            BuilderState.BODY_CONFIGURED,
        }:
            raise ValueError(
                "Authentication can only be set after method is configured"
            )
        if not api_key:
            raise ValueError("API key cannot be empty")
        self._authentication = Authentication(
            auth_type=AuthType.API_KEY,
            api_key=api_key,
            custom_headers={header_name: api_key},
        )
        self._transition_to_state(BuilderState.AUTH_CONFIGURED)
        return self

    def auth_custom(self, headers: Dict[str, str]) -> "HTTPRequestBuilder":
        """Set custom authentication headers"""
        # TODO: Implement
        if self._state not in {
            BuilderState.METHOD_SET,
            BuilderState.HEADERS_CONFIGURED,
            BuilderState.BODY_CONFIGURED,
        }:
            raise ValueError(
                "Authentication can only be set after method is configured"
            )
        if not headers:
            raise ValueError("Custom authentication headers cannot be empty")
        self._authentication = Authentication(
            auth_type=AuthType.CUSTOM, custom_headers=headers
        )
        self._transition_to_state(BuilderState.AUTH_CONFIGURED)
        return self

    # ========================================================================
    # POLICIES AND CONFIGURATION
    # ========================================================================

    def retry(
        self, strategy: RetryStrategy, max_attempts: int = 3, base_delay: float = 1.0
    ) -> "HTTPRequestBuilder":
        """Configure retry policy"""
        # TODO: Implement
        # - Create RetryPolicy object
        # - Validate configuration
        # - Transition to POLICIES_CONFIGURED state
        if self._state not in {
            BuilderState.METHOD_SET,
            BuilderState.HEADERS_CONFIGURED,
            BuilderState.BODY_CONFIGURED,
            BuilderState.AUTH_CONFIGURED,
        }:
            raise ValueError("Retry policy can only be set after method is configured")
        if not isinstance(strategy, RetryStrategy):
            raise ValueError("Invalid retry strategy")
        if max_attempts < 1:
            raise ValueError("max_attempts must be at least 1")
        if base_delay <= 0:
            raise ValueError("base_delay must be positive")
        self._retry_policy = RetryPolicy(
            strategy=strategy, max_attempts=max_attempts, base_delay_seconds=base_delay
        )
        self._transition_to_state(BuilderState.POLICIES_CONFIGURED)
        return self

    def timeout(
        self, connect: float = 30.0, read: float = 30.0, total: float = 60.0
    ) -> "HTTPRequestBuilder":
        """Configure timeout settings"""
        # TODO: Implement
        # - Create TimeoutConfig object
        # - Validate configuration
        if self._state not in {
            BuilderState.METHOD_SET,
            BuilderState.HEADERS_CONFIGURED,
            BuilderState.BODY_CONFIGURED,
            BuilderState.AUTH_CONFIGURED,
            BuilderState.POLICIES_CONFIGURED,
        }:
            raise ValueError(
                "Timeout configuration can only be set after method is configured"
            )
        if connect <= 0 or read <= 0 or total <= 0:
            raise ValueError("Timeout values must be positive")
        self._timeout_config = TimeoutConfig(
            connect_timeout_seconds=connect,
            read_timeout_seconds=read,
            total_timeout_seconds=total,
        )
        self._transition_to_state(BuilderState.POLICIES_CONFIGURED)
        return self

    def cache(
        self, strategy: CacheStrategy, ttl_seconds: int = 300
    ) -> "HTTPRequestBuilder":
        """Configure caching"""
        # TODO: Implement
        if self._state not in {
            BuilderState.METHOD_SET,
            BuilderState.HEADERS_CONFIGURED,
            BuilderState.BODY_CONFIGURED,
            BuilderState.AUTH_CONFIGURED,
        }:
            raise ValueError(
                "Cache configuration can only be set after method is configured"
            )
        if not isinstance(strategy, CacheStrategy):
            raise ValueError("Invalid cache strategy")
        if ttl_seconds < 0:
            raise ValueError("ttl_seconds must be non-negative")
        self._cache_config = CacheConfig(strategy=strategy, ttl_seconds=ttl_seconds)
        self._transition_to_state(BuilderState.POLICIES_CONFIGURED)
        return self

    def circuit_breaker(
        self, failure_threshold: int = 5, timeout_seconds: float = 60.0
    ) -> "HTTPRequestBuilder":
        """Configure circuit breaker"""
        # TODO: Implement
        if self._state not in {
            BuilderState.METHOD_SET,
            BuilderState.HEADERS_CONFIGURED,
            BuilderState.BODY_CONFIGURED,
            BuilderState.AUTH_CONFIGURED,
        }:
            raise ValueError(
                "Circuit breaker configuration can only be set after method is configured"
            )
        if failure_threshold < 1:
            raise ValueError("failure_threshold must be at least 1")
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        self._circuit_breaker = CircuitBreakerConfig(
            enabled=True,
            failure_threshold=failure_threshold,
            timeout_seconds=timeout_seconds,
        )
        self._transition_to_state(BuilderState.POLICIES_CONFIGURED)
        return self

    # ========================================================================
    # INTERCEPTORS
    # ========================================================================

    def add_request_interceptor(
        self, interceptor: RequestInterceptor
    ) -> "HTTPRequestBuilder":
        """Add request interceptor"""
        # TODO: Implement
        # - Add to interceptors list
        # - Maintain order for execution
        self._request_interceptors.append(interceptor)
        return self

    def add_response_interceptor(
        self, interceptor: ResponseInterceptor
    ) -> "HTTPRequestBuilder":
        """Add response interceptor"""
        # TODO: Implement
        self._response_interceptors.append(interceptor)
        return self

    def with_logging(self, log_level: str = "INFO") -> "HTTPRequestBuilder":
        """Enable request/response logging"""
        # TODO: Implement using LoggingInterceptor
        self.add_request_interceptor(LoggingInterceptor(log_level=log_level))
        return self

    def with_rate_limiting(self, requests_per_second: float) -> "HTTPRequestBuilder":
        """Enable rate limiting"""
        # TODO: Implement using RateLimitInterceptor
        self.add_request_interceptor(
            RateLimitInterceptor(requests_per_second=requests_per_second)
        )
        return self

    def with_request_signing(
        self, secret_key: str, algorithm: str = "HMAC-SHA256"
    ) -> "HTTPRequestBuilder":
        """Enable request signing"""
        # TODO: Implement using RequestSigningInterceptor
        self.add_request_interceptor(
            RequestSigningInterceptor(secret_key=secret_key, algorithm=algorithm)
        )
        return self

    # ========================================================================
    # BUILD AND EXECUTION
    # ========================================================================

    def build(self) -> HTTPRequest:
        """Build final HTTP request"""
        # TODO: Implement
        # - Validate all required components are set
        # - Run final comprehensive validation
        # - Apply all request interceptors
        # - Create immutable HTTPRequest
        # - Reset builder state
        self._run_validations()

        request = HTTPRequest(
            method=self._method,
            url=self._url,
            headers=self._headers,
            query_params=self._query_params,
            body=self._body,
            files=self._files,
            authentication=self._authentication,
            retry_policy=self._retry_policy,
            timeout_config=self._timeout_config,
            cache_config=self._cache_config,
            circuit_breaker=self._circuit_breaker,
        )
        errors = request.validate_complete_request()
        if errors:
            raise ValueError("Request validation errors: " + "; ".join(errors))

        for interceptor in self._request_interceptors:
            request = interceptor.intercept(request)

        self.reset()
        return request

    def build_and_execute(self) -> Any:
        """Build request and execute it"""
        # TODO: Implement
        # - Build request
        # - Execute with retry policy
        # - Apply response interceptors
        # - Handle circuit breaker logic
        # - Return response
        request = self.build()

        attempts = 0
        response = None
        while True:
            try:
                response = self._execute_http_request(request)
                break
            except Exception as e:
                attempts += 1
                if (
                    self._retry_policy.strategy == RetryStrategy.NONE
                    or attempts >= self._retry_policy.max_attempts
                ):
                    logger.error(f"Request failed after {attempts} attempts: {e}")
                    raise
                delay = self._retry_policy.get_delay(attempts)
                logger.warning(
                    f"Request failed (attempt {attempts}), retrying in {delay:.2f} seconds: {e}"
                )
                time.sleep(delay)

        for interceptor in self._response_interceptors:
            response = interceptor.intercept(response)
        return response

    # ========================================================================
    # UTILITY METHODS
    # ========================================================================

    def clone(self) -> "HTTPRequestBuilder":
        """Create a copy of current builder state"""
        # TODO: Implement deep copy of builder state
        new_builder = HTTPRequestBuilder()
        new_builder._state = self._state
        new_builder._method = self._method
        new_builder._url = self._url
        new_builder._headers = self._headers.copy()
        new_builder._query_params = self._query_params.copy()
        new_builder._body = self._body
        new_builder._files = self._files.copy()
        new_builder._authentication = self._authentication
        new_builder._retry_policy = self._retry_policy
        new_builder._timeout_config = self._timeout_config
        new_builder._cache_config = self._cache_config
        new_builder._circuit_breaker = self._circuit_breaker
        new_builder._request_interceptors = self._request_interceptors.copy()
        new_builder._response_interceptors = self._response_interceptors.copy()
        new_builder._operation_history = self._operation_history.copy()
        return new_builder

    def reset(self) -> "HTTPRequestBuilder":
        """Reset builder to initial state"""
        # TODO: Implement full reset
        self._state = BuilderState.INITIAL
        self._method = None
        self._url = ""
        self._headers.clear()
        self._query_params.clear()
        self._body = None
        self._files.clear()
        self._authentication = None
        self._retry_policy = RetryPolicy(RetryStrategy.NONE)
        self._timeout_config = TimeoutConfig()
        self._cache_config = CacheConfig(CacheStrategy.NONE)
        self._circuit_breaker = CircuitBreakerConfig()
        self._request_interceptors.clear()
        self._response_interceptors.clear()
        self._operation_history.clear()
        return self

    def get_current_state(self) -> BuilderState:
        """Get current builder state"""
        return self._state

    def get_operation_history(self) -> List[str]:
        """Get operation history for debugging"""
        return self._operation_history.copy()

    def to_curl(self) -> str:
        """Generate equivalent curl command"""
        # TODO: Implement curl command generation
        # - Convert all settings to curl flags
        # - Handle authentication
        # - Include headers and body
        curl_parts = ["curl"]
        if self._method:
            curl_parts.append(f"-X {self._method.value}")
        if self._headers:
            for name, value in self._headers.items():
                curl_parts.append(f"-H '{name}: {value}'")
        if self._body:
            if isinstance(self._body, str):
                curl_parts.append(f"-d '{self._body}'")
            elif isinstance(self._body, bytes):
                curl_parts.append(
                    f"--data-binary '{self._body.decode('utf-8', errors='ignore')}'"
                )
        if self._url:
            url_with_params = self._url
            if self._query_params:
                query_string = urlencode(self._query_params)
                separator = "&" if "?" in self._url else "?"
                url_with_params += f"{separator}{query_string}"
            curl_parts.append(f"'{url_with_params}'")
        return " ".join(curl_parts)


# ============================================================================
# DIRECTOR PATTERNS FOR COMMON REQUESTS
# ============================================================================


class HTTPRequestDirector:
    """Director for creating common HTTP request patterns"""

    def __init__(self, builder: HTTPRequestBuilder):
        self._builder = builder

    def json_api_request(
        self,
        method: HTTPMethod,
        url: str,
        data: Dict[str, Any] = None,
        api_key: str = None,
    ) -> HTTPRequest:
        """Create standard JSON API request"""
        # TODO: Implement
        # - Set JSON content type
        # - Add API key if provided
        # - Configure standard retry policy
        # - Add logging
        return (
            self._builder.reset()
            .url(url)
            .method(method)
            .content_type(ContentType.JSON)
            .auth_api_key(api_key)
            if api_key
            else self._builder.with_logging()
            .retry(RetryStrategy.EXPONENTIAL, max_attempts=3)
            .build()
        )

    def file_upload_request(
        self, url: str, files: List[FileUpload], form_data: Dict[str, str] = None
    ) -> HTTPRequest:
        """Create multipart file upload request"""
        # TODO: Implement
        # - Configure multipart/form-data
        # - Add files and form data
        # - Set appropriate timeouts
        return (
            self._builder.reset()
            .url(url)
            .post()
            .files(files)
            .body_form(form_data or {})
            .timeout(connect=10.0, read=120.0)
            .build()
        )

    def secure_api_request(
        self, method: HTTPMethod, url: str, secret_key: str, data: Dict[str, Any] = None
    ) -> HTTPRequest:
        """Create signed secure API request"""
        # TODO: Implement
        # - Add request signing
        # - Configure authentication
        # - Add security headers
        return (
            self._builder.reset()
            .url(url)
            .method(method)
            .body_json(data or {})
            .with_request_signing(secret_key=secret_key)
            .with_logging()
            .retry(RetryStrategy.EXPONENTIAL, max_attempts=3)
            .build()
        )

    def microservice_request(
        self,
        service_name: str,
        endpoint: str,
        method: HTTPMethod = HTTPMethod.GET,
        correlation_id: str = None,
    ) -> HTTPRequest:
        """Create microservice-to-microservice request"""
        # TODO: Implement
        # - Add correlation ID
        # - Configure circuit breaker
        # - Add distributed tracing headers
        # - Set reasonable timeouts
        if not correlation_id:
            correlation_id = str(uuid.uuid4())
        return (
            self._builder.reset()
            .url(f"http://{service_name}/{endpoint.lstrip('/')}")
            .method(method)
            .header("X-Correlation-ID", correlation_id)
            .circuit_breaker(failure_threshold=3, timeout_seconds=30.0)
            .timeout(connect=5.0, read=15.0)
            .build()
        )


# ============================================================================
# EXAMPLE USAGE AND TESTING
# ============================================================================

if __name__ == "__main__":
    builder = HTTPRequestBuilder()
    director = HTTPRequestDirector(builder)

    # Example 1: Simple GET request
    try:
        request = (
            builder.get("https://api.example.com/users")
            .header("Accept", "application/json")
            .query_param("page", "1")
            .query_param("limit", "10")
            .auth_bearer("your-token-here")
            .with_logging()
            .build()
        )

        print("✅ GET request built successfully")
        print(f"Method: {request.method}")
        print(f"URL: {request.url}")

    except Exception as e:
        print(f"❌ GET request failed: {e}")

    # Example 2: POST request with JSON body
    try:
        request = (
            builder.reset()
            .post("https://api.example.com/users")
            .content_type(ContentType.JSON)
            .body_json({"name": "John Doe", "email": "john@example.com"})
            .auth_api_key("your-api-key")
            .retry(RetryStrategy.EXPONENTIAL, max_attempts=3)
            .timeout(connect=10.0, read=30.0)
            .build()
        )

        print("✅ POST request built successfully")

    except Exception as e:
        print(f"❌ POST request failed: {e}")

    # Example 3: File upload
    try:
        file_upload = FileUpload(
            field_name="document",
            filename="report.pdf",
            content=b"fake pdf content",
            content_type="application/pdf",
        )

        request = (
            builder.reset()
            .post("https://api.example.com/upload")
            .file("document", "report.pdf", b"fake pdf content", "application/pdf")
            .with_request_signing("secret-key")
            .build()
        )

        print("✅ File upload request built successfully")

    except Exception as e:
        print(f"❌ File upload failed: {e}")

    # Example 4: Using director patterns
    try:
        api_request = director.json_api_request(
            HTTPMethod.GET, "https://api.example.com/data", api_key="your-api-key"
        )
        print("✅ Director API request created successfully")

    except Exception as e:
        print(f"❌ Director request failed: {e}")

    # Example 5: Generate curl command
    try:
        builder_for_curl = HTTPRequestBuilder()
        request = (
            builder_for_curl.get("https://httpbin.org/get")
            .header("User-Agent", "MyApp/1.0")
            .query_param("test", "value")
        )

        curl_command = builder_for_curl.to_curl()
        print(f"✅ Generated curl: {curl_command}")

    except Exception as e:
        print(f"❌ Curl generation failed: {e}")
