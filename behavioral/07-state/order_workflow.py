import threading
import time
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

# -----------------------------
# Constants
# -----------------------------
RETURN_WINDOW_SECONDS = 30 * 24 * 3600  # 30 days


# -----------------------------
# Domain Event & Error
# -----------------------------
@dataclass(frozen=True)
class Event:
    ts: float
    order_id: str
    action: str
    old_state: str
    new_state: str
    meta: Dict[str, Any] = field(default_factory=dict)


class OrderWorkflowError(Exception):
    """Domain-specific error for invalid state transitions."""


# -----------------------------
# Abstract State
# -----------------------------
class WorkflowState(ABC):
    _instances: Dict[type, "WorkflowState"] = {}
    _lock = threading.Lock()

    def __new__(cls):
        """Singleton pattern for stateless state objects."""
        if cls not in cls._instances:
            with cls._lock:
                if cls not in cls._instances:
                    cls._instances[cls] = super().__new__(cls)
        return cls._instances[cls]

    @property
    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    def pay(self, ctx: "OrderWF", meta: Dict[str, Any]): ...

    @abstractmethod
    def reserve_inventory(
        self, ctx: "OrderWF", items: List[str], meta: Dict[str, Any]
    ): ...

    @abstractmethod
    def ship(self, ctx: "OrderWF", meta: Dict[str, Any]): ...

    @abstractmethod
    def deliver(self, ctx: "OrderWF", meta: Dict[str, Any]): ...

    @abstractmethod
    def cancel(self, ctx: "OrderWF", meta: Dict[str, Any]): ...

    @abstractmethod
    def refund(self, ctx: "OrderWF", meta: Dict[str, Any]): ...


# -----------------------------
# Guard Functions
# -----------------------------
def payment_verified(ctx: "OrderWF") -> bool:
    # Payment is verified if we have a payment reference
    return ctx.payment_ref is not None


def stock_available(ctx: "OrderWF", items: List[str]) -> bool:
    # Placeholder: in real life, check inventory service; here: items list must be non-empty
    return bool(items)


def return_window_open(ctx: "OrderWF") -> bool:
    if ctx.delivered_at is None:
        return False
    return (time.time() - ctx.delivered_at) <= RETURN_WINDOW_SECONDS


# -----------------------------
# Context
# -----------------------------
class OrderWF:
    def __init__(self, order_id: str, on_transition=None):
        self.order_id = order_id
        self._state: WorkflowState = PendingWF()
        self.events: List[Event] = []
        self.on_transition = on_transition
        self._lock = threading.RLock()
        # domain fields:
        self.payment_ref: Optional[str] = None
        self.inventory_items: List[str] = []
        self.delivered_at: Optional[float] = None

    def set_state(self, state: WorkflowState, action: str, meta: Dict[str, Any] = None):
        with self._lock:
            old = self._state.name
            new = state.name
            self._state = state
            ev = Event(
                ts=time.time(),
                order_id=self.order_id,
                action=action,
                old_state=old,
                new_state=new,
                meta=meta or {},
            )
            self.events.append(ev)
            if self.on_transition:
                self.on_transition(self, ev)

    def state_name(self) -> str:
        with self._lock:
            return self._state.name

    # Delegation
    def pay(self, meta=None):
        with self._lock:
            self._state.pay(self, meta or {})

    def reserve_inventory(self, items: List[str], meta=None):
        with self._lock:
            self._state.reserve_inventory(self, items, meta or {})

    def ship(self, meta=None):
        with self._lock:
            self._state.ship(self, meta or {})

    def deliver(self, meta=None):
        with self._lock:
            self._state.deliver(self, meta or {})

    def cancel(self, meta=None):
        with self._lock:
            self._state.cancel(self, meta or {})

    def refund(self, meta=None):
        with self._lock:
            self._state.refund(self, meta or {})

    def to_dict(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "order_id": self.order_id,
                "state": self.state_name(),
                "events": [asdict(ev) for ev in self.events],
                "payment_ref": self.payment_ref,
                "inventory_items": self.inventory_items,
                "delivered_at": self.delivered_at,
            }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "OrderWF":
        state_map = {
            "PendingWF": PendingWF,
            "PaidWF": PaidWF,
            "InventoryReservedWF": InventoryReservedWF,
            "ShippedWF": ShippedWF,
            "DeliveredWF": DeliveredWF,
            "CancelledWF": CancelledWF,
            "RefundedWF": RefundedWF,
            "ErrorWF": ErrorWF,
        }
        state_name = data.get("state")
        if state_name not in state_map:
            raise OrderWorkflowError(f"Unknown state: {state_name}")

        obj = cls(order_id=data["order_id"])
        obj._state = state_map[state_name]()
        events = data.get("events", [])
        obj.events = [Event(**ev) for ev in events]
        obj.payment_ref = data.get("payment_ref")
        obj.inventory_items = data.get("inventory_items", [])
        obj.delivered_at = data.get("delivered_at")

        # Validate state consistency
        if state_name == "PaidWF" and not obj.payment_ref:
            raise OrderWorkflowError("PaidWF state requires payment_ref")
        if state_name == "InventoryReservedWF" and not obj.inventory_items:
            raise OrderWorkflowError(
                "InventoryReservedWF state requires inventory_items"
            )
        if state_name == "DeliveredWF" and not obj.delivered_at:
            raise OrderWorkflowError("DeliveredWF state requires delivered_at")

        return obj


# -----------------------------
# States
# -----------------------------
class PendingWF(WorkflowState):
    @property
    def name(self):
        return "PendingWF"

    def pay(self, ctx: OrderWF, meta: Dict[str, Any]):
        payment_ref = meta.get("payment_ref")
        if payment_ref:
            ctx.payment_ref = payment_ref
            ctx.set_state(PaidWF(), action="pay", meta=meta)
        else:
            ctx.set_state(ErrorWF(), action="pay_failed", meta=meta)

    def reserve_inventory(self, ctx, items, meta):
        raise OrderWorkflowError("Cannot reserve inventory in Pending")

    def ship(self, ctx, meta):
        raise OrderWorkflowError("Cannot ship in Pending")

    def deliver(self, ctx, meta):
        raise OrderWorkflowError("Cannot deliver in Pending")

    def cancel(self, ctx, meta):
        ctx.set_state(CancelledWF(), action="cancel", meta=meta)

    def refund(self, ctx, meta):
        raise OrderWorkflowError("Cannot refund in Pending")


class PaidWF(WorkflowState):
    @property
    def name(self):
        return "PaidWF"

    def pay(self, ctx, meta):
        raise OrderWorkflowError("Already paid")

    def reserve_inventory(self, ctx, items, meta):
        if stock_available(ctx, items):
            ctx.inventory_items = items
            ctx.set_state(InventoryReservedWF(), action="reserve_inventory", meta=meta)
        else:
            ctx.set_state(ErrorWF(), action="reserve_inventory_failed", meta=meta)

    def ship(self, ctx, meta):
        raise OrderWorkflowError("Cannot ship before reserving inventory")

    def deliver(self, ctx, meta):
        raise OrderWorkflowError("Cannot deliver before shipping")

    def cancel(self, ctx, meta):
        ctx.set_state(CancelledWF(), action="cancel", meta=meta)

    def refund(self, ctx, meta):
        ctx.set_state(RefundedWF(), action="refund", meta=meta)


class InventoryReservedWF(WorkflowState):
    @property
    def name(self):
        return "InventoryReservedWF"

    def pay(self, ctx, meta):
        raise OrderWorkflowError("Already paid")

    def reserve_inventory(self, ctx, items, meta):
        raise OrderWorkflowError("Inventory already reserved")

    def ship(self, ctx, meta):
        ctx.set_state(ShippedWF(), action="ship", meta=meta)

    def deliver(self, ctx, meta):
        raise OrderWorkflowError("Cannot deliver before shipping")

    def cancel(self, ctx, meta):
        ctx.set_state(CancelledWF(), action="cancel", meta=meta)

    def refund(self, ctx, meta):
        ctx.set_state(RefundedWF(), action="refund", meta=meta)


class ShippedWF(WorkflowState):
    @property
    def name(self):
        return "ShippedWF"

    def pay(self, ctx, meta):
        raise OrderWorkflowError("Already paid")

    def reserve_inventory(self, ctx, items, meta):
        raise OrderWorkflowError("Inventory already reserved")

    def ship(self, ctx, meta):
        raise OrderWorkflowError("Already shipped")

    def deliver(self, ctx, meta):
        ctx.delivered_at = time.time()
        ctx.set_state(DeliveredWF(), action="deliver", meta=meta)

    def cancel(self, ctx, meta):
        raise OrderWorkflowError("Cannot cancel after shipping")

    def refund(self, ctx, meta):
        ctx.set_state(RefundedWF(), action="refund", meta=meta)


class DeliveredWF(WorkflowState):
    @property
    def name(self):
        return "DeliveredWF"

    def pay(self, ctx, meta):
        raise OrderWorkflowError("Already paid")

    def reserve_inventory(self, ctx, items, meta):
        raise OrderWorkflowError("Inventory already reserved")

    def ship(self, ctx, meta):
        raise OrderWorkflowError("Already shipped")

    def deliver(self, ctx, meta):
        raise OrderWorkflowError("Already delivered")

    def cancel(self, ctx, meta):
        raise OrderWorkflowError("Cannot cancel after delivery")

    def refund(self, ctx, meta):
        if return_window_open(ctx):
            ctx.set_state(RefundedWF(), action="refund", meta=meta)
        else:
            raise OrderWorkflowError("Return window closed; cannot refund")


class CancelledWF(WorkflowState):
    @property
    def name(self):
        return "CancelledWF"

    def pay(self, ctx, meta):
        raise OrderWorkflowError("Order is cancelled")

    def reserve_inventory(self, ctx, items, meta):
        raise OrderWorkflowError("Order is cancelled")

    def ship(self, ctx, meta):
        raise OrderWorkflowError("Order is cancelled")

    def deliver(self, ctx, meta):
        raise OrderWorkflowError("Order is cancelled")

    def cancel(self, ctx, meta):
        raise OrderWorkflowError("Already cancelled")

    def refund(self, ctx, meta):
        # Allow refund only if payment exists
        if ctx.payment_ref:
            ctx.set_state(RefundedWF(), action="refund", meta=meta)
        else:
            raise OrderWorkflowError("No payment to refund")


class RefundedWF(WorkflowState):
    @property
    def name(self):
        return "RefundedWF"

    def pay(self, ctx, meta):
        raise OrderWorkflowError("Order is refunded")

    def reserve_inventory(self, ctx, items, meta):
        raise OrderWorkflowError("Order is refunded")

    def ship(self, ctx, meta):
        raise OrderWorkflowError("Order is refunded")

    def deliver(self, ctx, meta):
        raise OrderWorkflowError("Order is refunded")

    def cancel(self, ctx, meta):
        raise OrderWorkflowError("Order is refunded")

    def refund(self, ctx, meta):
        raise OrderWorkflowError("Already refunded")


class ErrorWF(WorkflowState):
    @property
    def name(self):
        return "ErrorWF"

    def pay(self, ctx, meta):
        # Allow retry from error state
        payment_ref = meta.get("payment_ref")
        if payment_ref:
            ctx.payment_ref = payment_ref
            ctx.set_state(PaidWF(), action="retry_pay", meta=meta)
        else:
            raise OrderWorkflowError("Payment failed again - no payment_ref provided")

    def reserve_inventory(self, ctx, items, meta):
        raise OrderWorkflowError("Cannot reserve inventory in error state")

    def ship(self, ctx, meta):
        raise OrderWorkflowError("Cannot ship in error state")

    def deliver(self, ctx, meta):
        raise OrderWorkflowError("Cannot deliver in error state")

    def cancel(self, ctx, meta):
        # Allow cancellation from error state
        ctx.set_state(CancelledWF(), action="cancel", meta=meta)

    def refund(self, ctx, meta):
        # Allow refund if payment exists
        if ctx.payment_ref:
            ctx.set_state(RefundedWF(), action="refund", meta=meta)
        else:
            raise OrderWorkflowError("No payment to refund")


# -----------------------------
# Example usage / quick checks
# -----------------------------
if __name__ == "__main__":
    order = OrderWF(order_id="ORDER123")

    print("Initial state:", order.state_name())
    order.pay(meta={"payment_ref": "PAY123"})
    print("After payment:", order.state_name())

    order.reserve_inventory(items=["item1", "item2"], meta={"warehouse": "WH1"})
    print("After reserving inventory:", order.state_name())

    order.ship(meta={"carrier": "UPS", "tracking_number": "1Z999AA10123456784"})
    print("After shipping:", order.state_name())

    order.deliver(meta={"delivered_by": "UPS"})
    print("After delivery:", order.state_name())

    # Within return window -> refund allowed
    order.refund(meta={"reason": "Customer returned item"})
    print("After refund:", order.state_name())

    print("Final order data:", order.to_dict())
