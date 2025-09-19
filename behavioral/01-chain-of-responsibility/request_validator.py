import json
import logging
import time
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional


class ValidationStatus(Enum):
    SUCCESS = "success"
    BLOCKED = "blocked"
    WARNING = "warning"


class ValidationResult:
    def __init__(
        self,
        status: ValidationStatus,
        reason: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ):
        self.status = status
        self.reason = reason
        self.context = context or {}
        self.timestamp = datetime.utcnow()

    def __str__(self):
        return f"ValidationResult(status={self.status.value}, reason={self.reason})"


class Request:
    def __init__(
        self,
        headers: Dict[str, str],
        path: str,
        method: str,
        body: Optional[Dict] = None,
        client_ip: Optional[str] = None,
    ):
        self.headers = headers
        self.path = path
        self.method = method
        self.body = body or {}
        self.context: Dict[str, Any] = {}
        self.client_ip = client_ip or "unknown"
        self.timestamp = datetime.utcnow()
        self.request_id = f"{int(time.time() * 1000000)}"  # Simple request ID

    def __str__(self):
        return f"Request({self.method} {self.path}, id={self.request_id})"


class AuthValidator(ABC):
    def __init__(self, name: Optional[str] = None):
        self._next: Optional[AuthValidator] = None
        self.name = name or self.__class__.__name__
        self.logger = logging.getLogger(f"auth.{self.name}")

    def set_next(self, validator: "AuthValidator") -> "AuthValidator":
        self._next = validator
        return validator

    @abstractmethod
    def _validate(self, request: Request) -> ValidationResult:
        """Perform the actual validation logic"""
        pass

    def handle(self, request: Request) -> ValidationResult:
        """Main entry point with logging and error handling"""
        self.logger.info(f"Processing {request}")

        try:
            result = self._validate(request)

            if result.status == ValidationStatus.SUCCESS:
                self.logger.info(f"✅ {self.name} passed for {request}")
                return self._forward(request)
            elif result.status == ValidationStatus.WARNING:
                self.logger.warning(f"⚠️ {self.name} warning: {result.reason}")
                return self._forward(request)  # Continue despite warning
            else:
                self.logger.error(f"❌ {self.name} blocked {request}: {result.reason}")
                return result

        except Exception as e:
            self.logger.error(f"💥 {self.name} error processing {request}: {str(e)}")
            return ValidationResult(
                ValidationStatus.BLOCKED, f"validator_error: {str(e)}"
            )

    def _forward(self, request: Request) -> ValidationResult:
        if self._next:
            return self._next.handle(request)
        return ValidationResult(ValidationStatus.SUCCESS, "chain_completed")


class APIKeyValidator(AuthValidator):
    def __init__(self, valid_keys: Optional[List[str]] = None):
        super().__init__()
        self.valid_keys = valid_keys or ["valid_api_key", "dev_api_key", "test_api_key"]

    def _validate(self, request: Request) -> ValidationResult:
        api_key = request.headers.get("X-API-Key")

        if not api_key:
            return ValidationResult(ValidationStatus.BLOCKED, "missing_api_key")

        if api_key not in self.valid_keys:
            return ValidationResult(ValidationStatus.BLOCKED, "invalid_api_key")

        # Store API key info in request context for downstream validators
        request.context["api_key"] = api_key
        request.context["api_key_type"] = "dev" if "dev" in api_key else "prod"

        return ValidationResult(ValidationStatus.SUCCESS)


class RateLimitValidator(AuthValidator):
    def __init__(self, limit: int = 100, window_seconds: int = 3600):
        super().__init__()
        self.requests: Dict[str, List[datetime]] = {}
        self.limit = limit
        self.window_seconds = window_seconds

    def _validate(self, request: Request) -> ValidationResult:
        # Use API key from context if available, otherwise fall back to client IP
        identifier = request.context.get("api_key", request.client_ip)

        now = datetime.utcnow()
        window_start = now - timedelta(seconds=self.window_seconds)

        # Clean old requests and add current one
        timestamps = self.requests.get(identifier, [])
        timestamps = [ts for ts in timestamps if ts > window_start]
        timestamps.append(now)
        self.requests[identifier] = timestamps

        request.context["requests_in_window"] = len(timestamps)

        if len(timestamps) > self.limit:
            return ValidationResult(
                ValidationStatus.BLOCKED,
                f"rate_limit_exceeded: {len(timestamps)}/{self.limit} requests in {self.window_seconds}s",
            )

        # Warning if approaching limit
        if len(timestamps) > self.limit * 0.8:
            return ValidationResult(
                ValidationStatus.WARNING,
                f"approaching_rate_limit: {len(timestamps)}/{self.limit} requests",
            )

        return ValidationResult(ValidationStatus.SUCCESS)


class PermissionValidator(AuthValidator):
    def __init__(self):
        super().__init__()
        self.role_permissions = {
            "admin": ["/admin", "/api", "/user"],
            "moderator": ["/api", "/user", "/moderate"],
            "user": ["/api/user", "/user"],
            "guest": ["/public"],
        }

    def _validate(self, request: Request) -> ValidationResult:
        user_role = request.headers.get("X-User-Role", "guest").lower()
        user_id = request.headers.get("X-User-ID")

        # Store user info in context
        request.context["user_role"] = user_role
        request.context["user_id"] = user_id

        allowed_paths = self.role_permissions.get(user_role, [])

        # Check if any allowed path matches the request path
        if not any(
            request.path.startswith(allowed_path) for allowed_path in allowed_paths
        ):
            return ValidationResult(
                ValidationStatus.BLOCKED,
                f"insufficient_permissions: role '{user_role}' cannot access '{request.path}'",
            )

        return ValidationResult(ValidationStatus.SUCCESS)


class JWTValidator(AuthValidator):
    def __init__(self, require_jwt: bool = True):
        super().__init__()
        self.require_jwt = require_jwt
        self.valid_tokens = ["valid_jwt_token", "admin_jwt_token", "user_jwt_token"]

    def _validate(self, request: Request) -> ValidationResult:
        auth_header = request.headers.get("Authorization")

        if not auth_header:
            if self.require_jwt:
                return ValidationResult(
                    ValidationStatus.BLOCKED, "missing_authorization_header"
                )
            return ValidationResult(ValidationStatus.WARNING, "no_jwt_provided")

        if not auth_header.startswith("Bearer "):
            return ValidationResult(
                ValidationStatus.BLOCKED, "invalid_authorization_format"
            )

        try:
            token = auth_header.split(" ", 1)[1]
        except IndexError:
            return ValidationResult(ValidationStatus.BLOCKED, "malformed_bearer_token")

        if token not in self.valid_tokens:
            return ValidationResult(ValidationStatus.BLOCKED, "invalid_jwt_token")

        # In real implementation, you'd decode JWT and extract claims
        request.context["jwt_token"] = token
        request.context["jwt_valid"] = True

        return ValidationResult(ValidationStatus.SUCCESS)


class AuthenticationChain:
    """Convenience wrapper for building and managing authentication chains"""

    def __init__(self):
        self.validators: List[AuthValidator] = []
        self.logger = logging.getLogger("auth.chain")

    def add_validator(self, validator: AuthValidator) -> "AuthenticationChain":
        if self.validators:
            self.validators[-1].set_next(validator)
        self.validators.append(validator)
        return self

    def authenticate(self, request: Request) -> ValidationResult:
        if not self.validators:
            return ValidationResult(
                ValidationStatus.BLOCKED, "no_validators_configured"
            )

        self.logger.info(f"🔐 Starting authentication for {request}")
        start_time = time.time()

        result = self.validators[0].handle(request)

        duration = time.time() - start_time
        self.logger.info(f"🏁 Authentication completed in {duration:.3f}s: {result}")

        return result


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Build authentication chain
    auth_chain = AuthenticationChain()
    auth_chain.add_validator(APIKeyValidator()).add_validator(
        RateLimitValidator(limit=3, window_seconds=10)
    ).add_validator(PermissionValidator()).add_validator(JWTValidator())

    # Test cases
    test_requests = [
        # Success case
        Request(
            headers={
                "X-API-Key": "valid_api_key",
                "X-User-Role": "admin",
                "X-User-ID": "admin123",
                "Authorization": "Bearer valid_jwt_token",
            },
            path="/admin/dashboard",
            method="GET",
            client_ip="192.168.1.100",
        ),
        # Permission denied
        Request(
            headers={
                "X-API-Key": "valid_api_key",
                "X-User-Role": "user",
                "Authorization": "Bearer valid_jwt_token",
            },
            path="/admin/dashboard",
            method="GET",
        ),
        # Invalid API key
        Request(
            headers={
                "X-API-Key": "invalid_key",
                "X-User-Role": "admin",
                "Authorization": "Bearer valid_jwt_token",
            },
            path="/admin/dashboard",
            method="GET",
        ),
    ]

    print("\n" + "=" * 50)
    print("🧪 TESTING AUTHENTICATION CHAIN")
    print("=" * 50)

    for i, request in enumerate(test_requests, 1):
        print(f"\n--- Test Case {i} ---")
        result = auth_chain.authenticate(request)
        print(f"Final Result: {result}")
        print(f"Request Context: {json.dumps(request.context, indent=2, default=str)}")

    # Rate limiting test
    print(f"\n--- Rate Limiting Test ---")
    rate_test_request = Request(
        headers={
            "X-API-Key": "valid_api_key",
            "X-User-Role": "user",
            "Authorization": "Bearer valid_jwt_token",
        },
        path="/api/user/profile",
        method="GET",
    )

    for i in range(5):
        result = auth_chain.authenticate(rate_test_request)
        print(f"Request {i+1}: {result.status.value} - {result.reason}")
        time.sleep(1)
