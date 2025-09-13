from __future__ import annotations

import time
import uuid
from abc import ABC, abstractmethod
from typing import Dict, Optional, Protocol, Tuple


# Implementor
class Gateway(Protocol):
    def authorize(self, amount: int, currency: str, metadata: Dict) -> str: ...
    def capture(self, auth_id: str, amount: int) -> str: ...
    def refund(self, capture_id: str, amount: Optional[int] = None) -> str: ...


# ConcreteImplementors
class StripeGateway:
    def authorize(self, amount: int, currency: str, metadata: Dict) -> str:
        print("[Stripe] authorize")
        return f"auth_{uuid.uuid4()}"

    def capture(self, auth_id: str, amount: int) -> str:
        print("[Stripe] capture")
        return f"cap_{uuid.uuid4()}"

    def refund(self, capture_id: str, amount: Optional[int] = None) -> str:
        print("[Stripe] refund")
        return f"ref_{uuid.uuid4()}"


class PayPalGateway:
    def authorize(self, amount: int, currency: str, metadata: Dict) -> str:
        print("[PayPal] authorize")
        return f"auth_{uuid.uuid4()}"

    def capture(self, auth_id: str, amount: int) -> str:
        print("[PayPal] capture")
        return f"cap_{uuid.uuid4()}"

    def refund(self, capture_id: str, amount: Optional[int] = None) -> str:
        print("[PayPal] refund")
        return f"ref_{uuid.uuid4()}"


# Decorators
class RetryingGateway:
    def __init__(self, inner: Gateway, retries: int = 2, delay: float = 0.2):
        self._inner = inner
        self._retries = retries
        self._delay = delay

    def authorize(self, amount, currency, metadata):
        for i in range(self._retries + 1):
            try:
                return self._inner.authorize(amount, currency, metadata)
            except Exception:
                if i == self._retries:
                    raise
                time.sleep(self._delay)

    def capture(self, auth_id, amount):
        for i in range(self._retries + 1):
            try:
                return self._inner.capture(auth_id, amount)
            except Exception:
                if i == self._retries:
                    raise
                time.sleep(self._delay)

    def refund(self, capture_id, amount=None):
        for i in range(self._retries + 1):
            try:
                return self._inner.refund(capture_id, amount)
            except Exception:
                if i == self._retries:
                    raise
                time.sleep(self._delay)


class LoggingGateway:
    def __init__(self, inner: Gateway):
        self._inner = inner

    def authorize(self, amount, currency, metadata):
        print(f"[Log] authorize {amount} {currency}")
        return self._inner.authorize(amount, currency, metadata)

    def capture(self, auth_id, amount):
        print(f"[Log] capture {auth_id} {amount}")
        return self._inner.capture(auth_id, amount)

    def refund(self, capture_id, amount=None):
        print(f"[Log] refund {capture_id} {amount}")
        return self._inner.refund(capture_id, amount)


# Abstraction
class PaymentFlow(ABC):
    def __init__(self, gateway: Gateway):
        self._gateway = gateway
        self._idempotency: Dict[str, Tuple[str, str]] = {}

    @abstractmethod
    def execute(self, amount: int, currency: str, metadata: Dict) -> Dict: ...

    def _once(self, key: str, fn):
        if key in self._idempotency:
            return self._idempotency[key]
        res = fn()
        self._idempotency[key] = res
        return res


class OneClickFlow(PaymentFlow):
    def execute(self, amount, currency, metadata):
        auth_id = self._gateway.authorize(amount, currency, metadata)
        cap_id = self._gateway.capture(auth_id, amount)
        return {"auth_id": auth_id, "capture_id": cap_id}


class SubscriptionFlow(PaymentFlow):
    def execute(self, amount, currency, metadata):
        # Idempotent charge by subscription_id + period
        key = f"{metadata['subscription_id']}:{metadata['period']}"

        def charge():
            auth_id = self._gateway.authorize(amount, currency, metadata)
            cap_id = self._gateway.capture(auth_id, amount)
            return (auth_id, cap_id)

        auth_id, cap_id = self._once(key, charge)
        return {"auth_id": auth_id, "capture_id": cap_id}


# Wiring
def build_gateway(
    kind: str, with_retry: bool = True, with_logging: bool = True
) -> Gateway:
    base: Gateway = StripeGateway() if kind == "stripe" else PayPalGateway()
    if with_retry:
        base = RetryingGateway(base)
    if with_logging:
        base = LoggingGateway(base)
    return base


if __name__ == "__main__":
    gw = build_gateway("stripe", with_retry=True, with_logging=True)
    flow = OneClickFlow(gw)
    result = flow.execute(1000, "USD", {"customer_id": "c_123"})
    print(result)
