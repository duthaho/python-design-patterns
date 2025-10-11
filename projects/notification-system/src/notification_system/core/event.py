"""
Base Event class - all domain events inherit from this.
Pattern: Base class for Template Method pattern in processors
"""

from abc import ABC
from datetime import datetime
from enum import Enum
from typing import Any, ClassVar, Dict, Optional, Set
from uuid import uuid4


class EventPriority(Enum):
    """Priority levels for events."""

    LOW = "low"
    MEDIUM = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class Event(ABC):
    """
    Base class for all events in the system.

    Responsibilities:
    - Unique identification
    - Timestamp tracking
    - Payload validation
    - Serialization
    """

    REQUIRED_PAYLOAD_FIELDS: ClassVar[Set[str]] = set()

    def __init__(
        self,
        event_type: str,
        payload: Dict[str, Any],
        priority: EventPriority = EventPriority.MEDIUM,
        event_id: Optional[str] = None,
        timestamp: Optional[datetime] = None,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.event_type = event_type
        self.payload = payload
        self.priority = priority
        self.event_id = event_id or str(uuid4())
        self.timestamp = timestamp or datetime.utcnow()
        self.user_id = user_id
        self.metadata = metadata or {}
        self.validate()

    def validate(self) -> None:
        """
        Validate the event payload contains required fields.
        Raise ValueError if invalid.
        """
        missing_fields = self.REQUIRED_PAYLOAD_FIELDS - self.payload.keys()
        if missing_fields:
            raise ValueError(
                f"Missing required payload fields for {self.event_type}: {missing_fields}"
            )
        self.validate_payload()

    def validate_payload(self) -> None:
        """
        Additional payload validation specific to event type.
        Raise ValueError if invalid.
        """
        pass

    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize event to dictionary for storage or transmission.
        Returns: Dict with event data
        """
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "timestamp": self.timestamp.isoformat(),
            "payload": self.payload,
            "priority": self.priority.value,
            "user_id": self.user_id,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Event":
        """
        Deserialize event from dictionary.
        Returns: Event instance
        """
        timestamp = datetime.fromisoformat(data["timestamp"])
        priority = EventPriority(data.get("priority", "MEDIUM"))
        return cls(
            event_type=data["event_type"],
            payload=data["payload"],
            priority=priority,
            event_id=data["event_id"],
            timestamp=timestamp,
            user_id=data.get("user_id"),
            metadata=data.get("metadata", {}),
        )

    def __repr__(self) -> str:
        return f"<Event {self.event_type} id={self.event_id} priority={self.priority.value} timestamp={self.timestamp.isoformat()}>"

    def __eq__(self, value):
        if not isinstance(value, Event):
            return False
        return self.event_id == value.event_id

    def __hash__(self):
        return hash(self.event_id)
