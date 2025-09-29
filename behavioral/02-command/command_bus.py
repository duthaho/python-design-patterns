import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


# ---------- Result wrapper ----------
class Result:
    def __init__(self, ok: bool, message: str = "", data: Optional[dict] = None):
        self.ok = ok
        self.message = message
        self.data = data or {}

    @staticmethod
    def ok(data=None):
        return Result(True, data=data)

    @staticmethod
    def fail(msg):
        return Result(False, message=msg)


# ---------- Command interface ----------
class DomainCommand(ABC):
    @abstractmethod
    def execute(self) -> Result: ...

    @abstractmethod
    def undo(self) -> Result: ...


# ---------- Parameters ----------
@dataclass(frozen=True)
class CreateOrderParams:
    customer_id: str
    items: list[tuple[str, int]]  # (sku, qty)
    idempotency_key: Optional[str] = None


# ---------- Repositories & Services ----------
class CustomerRepo:
    def __init__(self):
        self._customers = {"CUST1": "Alice", "CUST2": "Bob"}

    def exists(self, customer_id: str) -> bool:
        return customer_id in self._customers


class OrderRepo:
    def __init__(self):
        self._orders: dict[str, dict] = {}

    def save(self, order_id: str, order: dict):
        self._orders[order_id] = order

    def get(self, order_id: str) -> Optional[dict]:
        return self._orders.get(order_id)

    def delete(self, order_id: str):
        self._orders.pop(order_id, None)


class InventoryService:
    def __init__(self):
        self._stock: dict[str, int] = {"SKU1": 10, "SKU2": 5, "SKU3": 0}

    def reserve(self, sku: str, qty: int) -> bool:
        if self._stock.get(sku, 0) >= qty:
            self._stock[sku] -= qty
            return True
        return False

    def release(self, sku: str, qty: int) -> None:
        self._stock[sku] = self._stock.get(sku, 0) + qty


class AuditLog:
    def __init__(self):
        self.events: list[dict] = []

    def record(self, event: dict):
        event["timestamp"] = time.time()
        event["correlation_id"] = str(uuid.uuid4())
        self.events.append(event)


class IdempotencyStore:
    def __init__(self):
        self._records: dict[str, dict] = {}

    def exists(self, key: str) -> Optional[dict]:
        return self._records.get(key)

    def save(self, key: str, result: dict):
        self._records[key] = result


# ---------- Command Implementation ----------
class CreateOrderCommand(DomainCommand):
    def __init__(
        self,
        params: CreateOrderParams,
        order_repo: OrderRepo,
        inventory: InventoryService,
        audit: AuditLog,
        customers: CustomerRepo,
        idem: IdempotencyStore,
    ):
        self.params = params
        self.order_repo = order_repo
        self.inventory = inventory
        self.audit = audit
        self.customers = customers
        self.idem = idem
        self._order_id: Optional[str] = None
        self._reserved: list[tuple[str, int]] = []
        self._executed = False

    def execute(self) -> Result:
        # Validation
        if not self.customers.exists(self.params.customer_id):
            return Result.fail("Customer not found")
        if not self.params.items:
            return Result.fail("No items")

        # Idempotency check
        if self.params.idempotency_key:
            existing = self.idem.exists(self.params.idempotency_key)
            if existing:
                return Result.ok({"order_id": existing["order_id"], "reused": True})

        # Reserve inventory
        for sku, qty in self.params.items:
            if qty <= 0:
                return Result.fail(f"Invalid qty for {sku}")
            if not self.inventory.reserve(sku, qty):
                # Rollback previous reservations
                for rsku, rqty in self._reserved:
                    self.inventory.release(rsku, rqty)
                return Result.fail(f"Insufficient stock for {sku}")
            self._reserved.append((sku, qty))

        # Simulate possible failure before persistence
        if "FAIL" in self.params.customer_id:
            # rollback reservations
            for rsku, rqty in self._reserved:
                self.inventory.release(rsku, rqty)
            return Result.fail("Simulated failure before persistence")

        # Persist order
        self._order_id = f"ORD-{self.params.customer_id}-{len(self.audit.events)+1}"
        self.order_repo.save(
            self._order_id,
            {"customer": self.params.customer_id, "items": self.params.items},
        )
        self.audit.record(
            {
                "type": "OrderCreated",
                "order_id": self._order_id,
                "idempotency_key": self.params.idempotency_key,
            }
        )
        if self.params.idempotency_key:
            self.idem.save(self.params.idempotency_key, {"order_id": self._order_id})
        self._executed = True
        return Result.ok({"order_id": self._order_id})

    def undo(self) -> Result:
        if not self._executed:
            return Result.fail("Nothing to undo")
        if self._order_id:
            self.order_repo.delete(self._order_id)
        for sku, qty in self._reserved:
            self.inventory.release(sku, qty)
        self.audit.record({"type": "OrderCancelled", "order_id": self._order_id})
        self._executed = False
        return Result.ok({"undone": True})


# ---------- Command Bus ----------
class CommandBus:
    def __init__(self):
        self._history: list[DomainCommand] = []

    def dispatch(self, cmd: DomainCommand) -> Result:
        res = cmd.execute()
        if res.ok:
            self._history.append(cmd)
        return res

    def undo_last(self) -> Result:
        if not self._history:
            return Result.fail("No history")
        cmd = self._history.pop()
        return cmd.undo()


# ---------- Demo ----------
def demo():
    repo = OrderRepo()
    inv = InventoryService()
    audit = AuditLog()
    customers = CustomerRepo()
    idem = IdempotencyStore()
    bus = CommandBus()

    cmd = CreateOrderCommand(
        CreateOrderParams("CUST1", [("SKU1", 2), ("SKU2", 1)], idempotency_key="A1"),
        repo,
        inv,
        audit,
        customers,
        idem,
    )
    print(bus.dispatch(cmd).data)
    print(bus.undo_last().data)


if __name__ == "__main__":
    demo()
