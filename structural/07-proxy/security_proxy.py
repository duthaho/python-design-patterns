import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Role(Enum):
    GUEST = "guest"
    USER = "user"
    ADMIN = "admin"


@dataclass
class Session:
    user_id: int
    role: Role
    created_at: datetime
    expires_at: datetime

    def is_valid(self) -> bool:
        return datetime.now() < self.expires_at


@dataclass
class AccessLogEntry:
    timestamp: datetime
    user_id: int
    action: str
    resource_id: Optional[int]
    success: bool
    ip_address: Optional[str] = None

    def __str__(self) -> str:
        status = "SUCCESS" if self.success else "FAILED"
        resource = f" resource_id={self.resource_id}" if self.resource_id else ""
        return f"[{self.timestamp}] User {self.user_id}: {self.action}{resource} - {status}"


class UserServiceInterface(ABC):
    @abstractmethod
    def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    def update_user(self, user_id: int, data: Dict[str, Any]) -> bool:
        pass

    @abstractmethod
    def delete_user(self, user_id: int) -> bool:
        pass

    @abstractmethod
    def get_all_users(self) -> Dict[int, Dict[str, Any]]:
        pass


class UserService(UserServiceInterface):
    def __init__(self):
        # Mock user database
        self.users = {
            1: {
                "id": 1,
                "name": "Alice",
                "email": "alice@example.com",
                "role": "admin",
            },
            2: {"id": 2, "name": "Bob", "email": "bob@example.com", "role": "user"},
            3: {
                "id": 3,
                "name": "Charlie",
                "email": "charlie@example.com",
                "role": "user",
            },
        }

    def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        logger.info(f"Retrieving user {user_id} from database")
        return self.users.get(user_id)

    def update_user(self, user_id: int, data: Dict[str, Any]) -> bool:
        if user_id in self.users:
            logger.info(f"Updating user {user_id} with data: {data}")
            self.users[user_id].update(data)
            return True
        return False

    def delete_user(self, user_id: int) -> bool:
        if user_id in self.users:
            logger.info(f"Deleting user {user_id}")
            del self.users[user_id]
            return True
        return False

    def get_all_users(self) -> Dict[int, Dict[str, Any]]:
        logger.info("Retrieving all users from database")
        return self.users.copy()


class SecurityError(Exception):
    """Base exception for security-related errors"""

    pass


class AuthenticationError(SecurityError):
    """Raised when authentication fails"""

    pass


class AuthorizationError(SecurityError):
    """Raised when authorization fails"""

    pass


class RateLimitError(SecurityError):
    """Raised when rate limit is exceeded"""

    pass


class SecurityProxy(UserServiceInterface):
    def __init__(
        self, user_service: UserServiceInterface, rate_limit_per_minute: int = 10
    ):
        self.user_service = user_service
        self.rate_limit_per_minute = rate_limit_per_minute
        self.sessions: Dict[str, Session] = {}
        self.access_log: List[AccessLogEntry] = []
        self.rate_limit_tracker: Dict[int, Tuple[int, datetime]] = {}

    def create_session(self, user_id: int, role: Role, duration_hours: int = 24) -> str:
        """Create a new session token"""
        import uuid

        token = str(uuid.uuid4())
        expires_at = datetime.now() + timedelta(hours=duration_hours)
        self.sessions[token] = Session(
            user_id=user_id, role=role, created_at=datetime.now(), expires_at=expires_at
        )
        logger.info(f"Created session for user {user_id} with role {role.value}")
        return token

    def _authenticate(self, session_token: str) -> Session:
        """Authenticate user and return session info"""
        if not session_token:
            raise AuthenticationError("Session token required")

        session = self.sessions.get(session_token)
        if not session:
            raise AuthenticationError("Invalid session token")

        if not session.is_valid():
            del self.sessions[session_token]
            raise AuthenticationError("Session expired")

        return session

    def _check_rate_limit(self, user_id: int) -> None:
        """Check if user has exceeded rate limit"""
        now = datetime.now()

        if user_id in self.rate_limit_tracker:
            count, reset_time = self.rate_limit_tracker[user_id]

            if now < reset_time:
                if count >= self.rate_limit_per_minute:
                    raise RateLimitError(
                        f"Rate limit exceeded. Try again after {reset_time}"
                    )
                self.rate_limit_tracker[user_id] = (count + 1, reset_time)
            else:
                # Reset the counter
                self.rate_limit_tracker[user_id] = (1, now + timedelta(minutes=1))
        else:
            self.rate_limit_tracker[user_id] = (1, now + timedelta(minutes=1))

    def _authorize_user_access(
        self, requesting_user_id: int, role: Role, target_user_id: int, action: str
    ) -> None:
        """Check if user is authorized to access target user's data"""
        # Admins can access everything
        if role == Role.ADMIN:
            return

        # Users can only access their own data
        if role == Role.USER and requesting_user_id == target_user_id:
            return

        # Special case: users can read their own data but may have restrictions on other operations
        if action in ["delete_user"] and role != Role.ADMIN:
            raise AuthorizationError(f"Insufficient privileges for {action}")

        if requesting_user_id != target_user_id:
            raise AuthorizationError("Access denied: can only access your own data")

    def _authorize_admin_only(self, role: Role, action: str) -> None:
        """Check if user has admin privileges for admin-only actions"""
        if role != Role.ADMIN:
            raise AuthorizationError(f"Admin privileges required for {action}")

    def _log_access(
        self,
        user_id: int,
        action: str,
        success: bool,
        resource_id: Optional[int] = None,
    ) -> None:
        """Log access attempt"""
        entry = AccessLogEntry(
            timestamp=datetime.now(),
            user_id=user_id,
            action=action,
            resource_id=resource_id,
            success=success,
        )
        self.access_log.append(entry)

        # Log to standard logger as well
        if success:
            logger.info(f"Access granted: {entry}")
        else:
            logger.warning(f"Access denied: {entry}")

    def get_user(self, session_token: str, user_id: int) -> Optional[Dict[str, Any]]:
        session = self._authenticate(session_token)

        try:
            self._check_rate_limit(session.user_id)
            self._authorize_user_access(
                session.user_id, session.role, user_id, "get_user"
            )

            result = self.user_service.get_user(user_id)
            self._log_access(session.user_id, "get_user", True, user_id)
            return result

        except (RateLimitError, AuthorizationError) as e:
            self._log_access(session.user_id, "get_user", False, user_id)
            raise

    def update_user(
        self, session_token: str, user_id: int, data: Dict[str, Any]
    ) -> bool:
        session = self._authenticate(session_token)

        try:
            self._check_rate_limit(session.user_id)
            self._authorize_user_access(
                session.user_id, session.role, user_id, "update_user"
            )

            result = self.user_service.update_user(user_id, data)
            self._log_access(session.user_id, "update_user", True, user_id)
            return result

        except (RateLimitError, AuthorizationError) as e:
            self._log_access(session.user_id, "update_user", False, user_id)
            raise

    def delete_user(self, session_token: str, user_id: int) -> bool:
        session = self._authenticate(session_token)

        try:
            self._check_rate_limit(session.user_id)
            self._authorize_admin_only(session.role, "delete_user")

            result = self.user_service.delete_user(user_id)
            self._log_access(session.user_id, "delete_user", True, user_id)
            return result

        except (RateLimitError, AuthorizationError) as e:
            self._log_access(session.user_id, "delete_user", False, user_id)
            raise

    def get_all_users(self, session_token: str) -> Dict[int, Dict[str, Any]]:
        session = self._authenticate(session_token)

        try:
            self._check_rate_limit(session.user_id)
            self._authorize_admin_only(session.role, "get_all_users")

            result = self.user_service.get_all_users()
            self._log_access(session.user_id, "get_all_users", True)
            return result

        except (RateLimitError, AuthorizationError) as e:
            self._log_access(session.user_id, "get_all_users", False)
            raise

    def get_access_log(
        self, session_token: str, limit: int = 100
    ) -> List[AccessLogEntry]:
        """Get access log (admin only)"""
        session = self._authenticate(session_token)
        self._authorize_admin_only(session.role, "get_access_log")
        return self.access_log[-limit:]

    def cleanup_expired_sessions(self) -> int:
        """Remove expired sessions and return count of removed sessions"""
        expired_tokens = [
            token for token, session in self.sessions.items() if not session.is_valid()
        ]

        for token in expired_tokens:
            del self.sessions[token]

        logger.info(f"Cleaned up {len(expired_tokens)} expired sessions")
        return len(expired_tokens)


def main() -> None:
    # Create services
    user_service = UserService()
    proxy = SecurityProxy(user_service, rate_limit_per_minute=5)  # Lower limit for demo

    # Create sessions
    admin_token = proxy.create_session(1, Role.ADMIN)
    user_token = proxy.create_session(2, Role.USER)
    guest_token = proxy.create_session(3, Role.GUEST)

    print("=== Security Proxy Demo ===\n")

    # Test 1: Admin accessing all users
    print("1. Admin accessing all users:")
    try:
        users = proxy.get_all_users(admin_token)
        print(f"Success: Found {len(users)} users")
    except SecurityError as e:
        print(f"Error: {e}")

    # Test 2: User accessing own data
    print("\n2. User accessing own data:")
    try:
        user = proxy.get_user(user_token, 2)
        print(f"Success: {user['name']} - {user['email']}")
    except SecurityError as e:
        print(f"Error: {e}")

    # Test 3: User trying to access another user's data
    print("\n3. User trying to access another user's data:")
    try:
        user = proxy.get_user(user_token, 1)
        print(f"Success: {user}")
    except SecurityError as e:
        print(f"Error: {e}")

    # Test 4: User trying to delete (admin-only operation)
    print("\n4. User trying to delete (admin-only):")
    try:
        result = proxy.delete_user(user_token, 3)
        print(f"Success: {result}")
    except SecurityError as e:
        print(f"Error: {e}")

    # Test 5: Rate limiting
    print("\n5. Testing rate limiting (making 6 requests quickly):")
    for i in range(6):
        try:
            proxy.get_user(user_token, 2)
            print(f"Request {i+1}: Success")
        except SecurityError as e:
            print(f"Request {i+1}: Error - {e}")

    # Test 6: Invalid token
    print("\n6. Testing invalid token:")
    try:
        proxy.get_user("invalid_token", 1)
    except SecurityError as e:
        print(f"Error: {e}")

    # Show access log
    print("\n=== Access Log ===")
    log_entries = proxy.get_access_log(admin_token)
    for entry in log_entries[-10:]:  # Show last 10 entries
        print(entry)


if __name__ == "__main__":
    main()
