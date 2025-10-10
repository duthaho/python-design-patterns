"""
Notification represents a message to be sent through a channel.
Pattern: Data Transfer Object (DTO)
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4


class NotificationStatus(Enum):
    """Status of a notification delivery"""

    PENDING = "pending"
    SCHEDULED = "scheduled"
    PROCESSING = "processing"
    SENT = "sent"
    FAILED = "failed"
    RETRYING = "retrying"


@dataclass
class NotificationResult:
    """
    Result of sending a notification through a channel.
    """

    success: bool
    channel: str
    message: Optional[str] = None
    sent_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Set sent_at to now if success and not provided"""
        if self.success and self.sent_at is None:
            self.sent_at = datetime.utcnow()


@dataclass
class Notification:
    """
    Represents a notification to be sent.
    """

    # Required fields
    event_id: str
    channel: str
    recipients: List[str]  # Multiple recipients!
    body: str

    # Optional fields with defaults
    notification_id: str = field(default_factory=lambda: str(uuid4()))
    subject: Optional[str] = None
    template: Optional[str] = None
    template_data: Dict[str, Any] = field(default_factory=dict)
    status: NotificationStatus = NotificationStatus.PENDING
    created_at: datetime = field(default_factory=datetime.utcnow)
    sent_at: Optional[datetime] = None
    send_after: Optional[datetime] = None  # Scheduling!
    retry_count: int = 0
    max_retries: int = 3
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Post-initialization validation"""
        if self.send_after and self.send_after > datetime.utcnow():
            self.status = NotificationStatus.SCHEDULED
        if self.send_after and self.send_after <= datetime.utcnow():
            self.send_after = None  # Clear past send_after
        if not self.recipients:
            raise ValueError("Recipients list cannot be empty")
        if not self.channel:
            raise ValueError("Channel cannot be empty")

    def can_retry(self) -> bool:
        """Check if notification can be retried"""
        return self.retry_count < self.max_retries and self.status in {
            NotificationStatus.FAILED,
            NotificationStatus.RETRYING,
        }

    def should_send_now(self) -> bool:
        """Check if notification should be sent now"""
        return self.send_after is None or self.send_after <= datetime.utcnow()

    def mark_sent(self, result: NotificationResult) -> None:
        """Mark notification as sent"""
        self.status = NotificationStatus.SENT
        self.sent_at = result.sent_at or datetime.utcnow()
        self.metadata.update(result.metadata)

    def mark_failed(self, error: str) -> None:
        """Mark notification as failed"""
        self.status = NotificationStatus.FAILED
        self.metadata["last_error"] = error
        self.metadata["last_failure_at"] = datetime.utcnow().isoformat()

    def increment_retry(self) -> None:
        """Increment retry count and set status to RETRYING"""
        self.retry_count += 1
        self.status = NotificationStatus.RETRYING

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary"""
        return {
            "notification_id": self.notification_id,
            "event_id": self.event_id,
            "channel": self.channel,
            "recipients": self.recipients,
            "subject": self.subject,
            "body": self.body,
            "template": self.template,
            "template_data": self.template_data,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "send_after": self.send_after.isoformat() if self.send_after else None,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Notification":
        """Deserialize from dictionary"""
        data["created_at"] = datetime.fromisoformat(data["created_at"])
        if data.get("sent_at"):
            data["sent_at"] = datetime.fromisoformat(data["sent_at"])
        if data.get("send_after"):
            data["send_after"] = datetime.fromisoformat(data["send_after"])
        data["status"] = NotificationStatus(data["status"])
        return cls(**data)