import random
import time
from dataclasses import dataclass
from functools import wraps
from typing import Any, Callable, Dict, List, Set


# ---------------- Domain Event ----------------
@dataclass(frozen=True)
class UserRegistered:
    id: int
    email: str
    ts: float


# ---------------- Infrastructure ----------------
class DomainEventBus:
    def __init__(self) -> None:
        self._handlers: Dict[type, List[Callable[[Any], None]]] = {}

    def subscribe(self, event_type: type, handler: Callable[[Any], None]) -> None:
        self._handlers.setdefault(event_type, []).append(handler)

    def publish(self, event: Any) -> None:
        for h in list(self._handlers.get(type(event), [])):
            try:
                h(event)
            except Exception as e:
                # h.__name__ is preserved by wraps in our decorators
                print(f"[domain] handler {h.__name__} failed: {e}")


class IdempotencyStore:
    def __init__(self) -> None:
        self._processed: Set[str] = set()

    def seen(self, key: str) -> bool:
        return key in self._processed

    def mark(self, key: str) -> None:
        self._processed.add(key)


# ---------------- Retry + DLQ ----------------
class RetryPolicy:
    def __init__(self, retries: int = 3) -> None:
        self.retries = retries
        self.dlq: List[Any] = []

    def wrap(self, handler: Callable[[Any], None]) -> Callable[[Any], None]:
        @wraps(handler)
        def wrapped(event: Any) -> None:
            attempts = 0
            while attempts < self.retries:
                try:
                    handler(event)
                    return
                except Exception as e:
                    attempts += 1
                    print(f"[retry] {handler.__name__} failed attempt {attempts}: {e}")
                    time.sleep(0.1 * attempts)  # simple backoff
            print(f"[DLQ] {handler.__name__} -> {event}")
            self.dlq.append((handler.__name__, event))

        return wrapped


# ---------------- Runtime Config ----------------
class HandlerConfig:
    def __init__(self) -> None:
        self.enabled: Dict[str, bool] = {}

    def enable(self, handler_name: str) -> None:
        self.enabled[handler_name] = True

    def disable(self, handler_name: str) -> None:
        self.enabled[handler_name] = False

    def wrap(self, handler: Callable[[Any], None]) -> Callable[[Any], None]:
        @wraps(handler)
        def wrapped(event: Any) -> None:
            # Use preserved handler.__name__ for config lookup
            if self.enabled.get(handler.__name__, True):
                handler(event)
            else:
                print(f"[config] {handler.__name__} disabled, skipping")

        return wrapped


# ---------------- Handlers ----------------
def send_welcome_email(e: UserRegistered) -> None:
    if random.random() < 0.2:  # simulate occasional failure
        raise RuntimeError("SMTP error")
    print(f"Sending welcome email to {e.email}")


def write_audit_log(e: UserRegistered) -> None:
    print(f"Audit: user {e.id} registered at {e.ts}")


def update_analytics(e: UserRegistered) -> None:
    print(f"Analytics: user_count+1")


# ---------------- Application Service ----------------
class UserService:
    def __init__(self, bus: DomainEventBus, idem: IdempotencyStore) -> None:
        self.bus = bus
        self.idem = idem
        self._users: Dict[int, str] = {}

    def register_user(self, id: int, email: str) -> None:
        # Simulate DB commit
        self._users[id] = email
        print(f"[db] committed user {id}")
        # After commit, publish event
        event = UserRegistered(id=id, email=email, ts=time.time())
        self.bus.publish(event)


# ---------------- Wiring ----------------
bus = DomainEventBus()
idem = IdempotencyStore()
retry_policy = RetryPolicy(retries=3)
config = HandlerConfig()


# Idempotency wrapper
def idempotent(
    handler: Callable[[UserRegistered], None],
) -> Callable[[UserRegistered], None]:
    @wraps(handler)
    def wrapped(e: UserRegistered) -> None:
        # Use preserved handler name in idempotency key
        key = f"{handler.__name__}:{e.id}"
        if idem.seen(key):
            print(f"[idem] skip {key}")
            return
        handler(e)
        idem.mark(key)

    return wrapped


# Compose: retry -> config -> idempotent (each uses @wraps to preserve original name)
for h in [send_welcome_email, write_audit_log, update_analytics]:
    wrapped = idempotent(config.wrap(retry_policy.wrap(h)))
    bus.subscribe(UserRegistered, wrapped)
    config.enable(h.__name__)  # enable all by default


# ---------------- Demo ----------------
if __name__ == "__main__":
    svc = UserService(bus, idem)

    print("\n--- First registration ---")
    svc.register_user(1, "duong@example.com")

    print("\n--- Duplicate registration (idempotent skip) ---")
    svc.register_user(1, "duong@example.com")

    print("\n--- Disable analytics handler ---")
    config.disable("update_analytics")
    svc.register_user(2, "another@example.com")

    print("\n--- DLQ contents ---")
    print(retry_policy.dlq)
