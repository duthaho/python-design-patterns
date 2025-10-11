"""
Order-related event classes.
"""

from typing import Any, ClassVar, Dict, Set

from ..core.event import Event, EventPriority


class OrderPlacedEvent(Event):
    """
    Event triggered when an order is placed.

    Required payload fields:
    - order_id: str
    - customer_name: str
    - customer_email: str
    - total_amount: float
    - item_count: int
    """

    REQUIRED_PAYLOAD_FIELDS: ClassVar[Set[str]] = {
        "order_id",
        "customer_name",
        "customer_email",
        "total_amount",
        "item_count",
    }

    def __init__(
        self,
        order_id: str,
        customer_name: str,
        customer_email: str,
        total_amount: float,
        item_count: int,
        user_id: str = None,
        metadata: Dict[str, Any] = None,
        **extra_fields,
    ):
        """Initialize OrderPlacedEvent."""
        payload = {
            "order_id": order_id,
            "customer_name": customer_name,
            "customer_email": customer_email,
            "total_amount": total_amount,
            "item_count": item_count,
            **extra_fields,
        }

        super().__init__(
            event_type="order.placed",
            payload=payload,
            priority=EventPriority.HIGH,
            user_id=user_id,
            metadata=metadata,
        )

    def validate_payload(self) -> None:
        """Validate order placed event."""
        # Total amount validation
        total_amount = self.payload.get("total_amount", -1)
        if not isinstance(total_amount, (int, float)) or total_amount < 0:
            raise ValueError(f"Invalid total_amount: {total_amount}")

        # Item count validation
        item_count = self.payload.get("item_count", 0)
        if not isinstance(item_count, int) or item_count <= 0:
            raise ValueError(f"Invalid item_count: {item_count}")

        # Email validation
        email = self.payload.get("customer_email", "")
        if "@" not in email:
            raise ValueError(f"Invalid customer_email: {email}")


class OrderShippedEvent(Event):
    """
    Event triggered when an order ships.

    Required payload fields:
    - order_id: str
    - customer_email: str
    - tracking_number: str
    - carrier: str
    """

    REQUIRED_PAYLOAD_FIELDS: ClassVar[Set[str]] = {
        "order_id",
        "customer_email",
        "tracking_number",
        "carrier",
    }

    def __init__(
        self,
        order_id: str,
        customer_email: str,
        tracking_number: str,
        carrier: str = "Standard",
        user_id: str = None,
        metadata: Dict[str, Any] = None,
        **extra_fields,
    ):
        """Initialize OrderShippedEvent."""
        payload = {
            "order_id": order_id,
            "customer_email": customer_email,
            "tracking_number": tracking_number,
            "carrier": carrier,
            **extra_fields,
        }

        super().__init__(
            event_type="order.shipped",
            payload=payload,
            priority=EventPriority.MEDIUM,
            user_id=user_id,
            metadata=metadata,
        )

    def validate_payload(self) -> None:
        """Validate order shipped event."""
        # Tracking number validation
        tracking_number = self.payload.get("tracking_number", "")
        if not tracking_number or not tracking_number.strip():
            raise ValueError("Tracking number cannot be empty")

        # Email validation
        email = self.payload.get("customer_email", "")
        if "@" not in email:
            raise ValueError(f"Invalid customer_email: {email}")
