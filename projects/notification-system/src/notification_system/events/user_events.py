"""
User-related event classes.
Pattern: Concrete implementations of Event base class
"""

from datetime import datetime
from typing import Any, ClassVar, Dict, Set

from ..core.event import Event, EventPriority


class UserSignupEvent(Event):
    """
    Event triggered when a new user signs up.

    Required payload fields:
    - username: str
    - email: str
    - signup_date: str (ISO format)
    """

    REQUIRED_PAYLOAD_FIELDS: ClassVar[Set[str]] = {"username", "email", "signup_date"}

    def __init__(
        self,
        username: str,
        email: str,
        signup_date: str = None,
        user_id: str = None,
        metadata: Dict[str, Any] = None,
        **extra_fields,
    ):
        """Initialize UserSignupEvent."""
        # Build payload
        payload = {
            "username": username,
            "email": email,
            "signup_date": signup_date or datetime.utcnow().isoformat(),
            "app_name": "NotificationSystem",  # For template
            **extra_fields,
        }

        # Call parent with string event_type
        super().__init__(
            event_type="user.signup",
            payload=payload,
            priority=EventPriority.HIGH,
            user_id=user_id,
            metadata=metadata,
        )

    def validate_payload(self) -> None:
        """Additional validation for user signup."""
        # Email validation
        email = self.payload.get("email", "")
        if "@" not in email or "." not in email:
            raise ValueError(f"Invalid email format: {email}")

        # Username validation
        username = self.payload.get("username", "")
        if not username or not username.strip():
            raise ValueError("Username cannot be empty")

        # Date validation
        signup_date = self.payload.get("signup_date", "")
        try:
            datetime.fromisoformat(signup_date)
        except (ValueError, TypeError):
            raise ValueError(f"Invalid signup_date format: {signup_date}")

    @property
    def username(self) -> str:
        """Get username from payload."""
        return self.payload["username"]

    @property
    def email(self) -> str:
        """Get email from payload."""
        return self.payload["email"]


class UserPasswordResetEvent(Event):
    """
    Event triggered when user requests password reset.

    Required payload fields:
    - username: str
    - email: str
    - reset_url: str
    - expiry_hours: int
    """

    REQUIRED_PAYLOAD_FIELDS: ClassVar[Set[str]] = {
        "username",
        "email",
        "reset_url",
        "expiry_hours",
    }

    def __init__(
        self,
        username: str,
        email: str,
        reset_url: str,
        expiry_hours: int = 24,
        user_id: str = None,
        metadata: Dict[str, Any] = None,
        **extra_fields,
    ):
        """Initialize UserPasswordResetEvent."""
        payload = {
            "username": username,
            "email": email,
            "reset_url": reset_url,
            "expiry_hours": expiry_hours,
            **extra_fields,
        }

        super().__init__(
            event_type="user.password_reset",
            payload=payload,
            priority=EventPriority.CRITICAL,
            user_id=user_id,
            metadata=metadata,
        )

    def validate_payload(self) -> None:
        """Validate password reset event."""
        # Email validation
        email = self.payload.get("email", "")
        if "@" not in email:
            raise ValueError(f"Invalid email format: {email}")

        # Reset URL validation
        reset_url = self.payload.get("reset_url", "")
        if not reset_url or not reset_url.startswith("http"):
            raise ValueError(f"Invalid reset URL: {reset_url}")

        # Expiry hours validation
        expiry_hours = self.payload.get("expiry_hours", 0)
        if not isinstance(expiry_hours, int) or expiry_hours <= 0:
            raise ValueError(f"Invalid expiry_hours: {expiry_hours}")
