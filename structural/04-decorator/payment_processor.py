import logging
import threading
import time
from typing import Dict, NamedTuple, Optional, Protocol, Tuple

# --- Logging setup ---
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())


# --- Domain Models ---
class ChargeRequest(NamedTuple):
    customer_id: str
    amount: float
    idempotency_key: Optional[str] = None


class Receipt(NamedTuple):
    id: str
    customer_id: str
    amount: float
    timestamp: float


# --- Custom Exceptions ---
class FraudDetectedError(Exception):
    pass


class RateLimitExceededError(Exception):
    pass


# --- PaymentProcessor Protocol ---
class PaymentProcessor(Protocol):
    def charge(self, request: ChargeRequest) -> Receipt: ...


# --- Base Implementation ---
class FakeProcessor:
    """Simulates a payment processor (e.g., Stripe) for testing."""

    def __init__(self) -> None:
        self._counter = 0

    def charge(self, request: ChargeRequest) -> Receipt:
        self._counter += 1
        logger.info(f"[BASE] Charging {request.amount} for {request.customer_id}")
        return Receipt(
            id=f"rcpt_{self._counter}",
            customer_id=request.customer_id,
            amount=request.amount,
            timestamp=time.time(),
        )


# --- Base Decorator ---
class ProcessorDecorator(PaymentProcessor):
    def __init__(self, wrapped: PaymentProcessor) -> None:
        self._wrapped = wrapped

    def charge(self, request: ChargeRequest) -> Receipt:
        return self._wrapped.charge(request)


# --- Idempotency Decorator ---
class IdempotencyDecorator(ProcessorDecorator):
    def __init__(
        self,
        wrapped: PaymentProcessor,
        enforce_key: bool = False,
        ttl_seconds: Optional[float] = None,
    ) -> None:
        super().__init__(wrapped)
        self._cache: Dict[Tuple[str, str], Tuple[float, Receipt]] = {}
        self.enforce_key = enforce_key
        self.ttl_seconds = ttl_seconds

    def charge(self, request: ChargeRequest) -> Receipt:
        if self.enforce_key and not request.idempotency_key:
            raise ValueError("[IDEMPOTENCY] Missing idempotency key")

        if request.idempotency_key:
            key = (request.customer_id, request.idempotency_key)
            now = time.time()
            if key in self._cache:
                ts, receipt = self._cache[key]
                if self.ttl_seconds is None or now - ts <= self.ttl_seconds:
                    logger.info("[IDEMPOTENCY] Returning cached receipt")
                    return receipt
                else:
                    logger.info("[IDEMPOTENCY] Cache expired, processing again")
            receipt = super().charge(request)
            self._cache[key] = (now, receipt)
            return receipt
        else:
            return super().charge(request)


# --- Fraud Check Decorator ---
class FraudCheckDecorator(ProcessorDecorator):
    def __init__(self, wrapped: PaymentProcessor, threshold: float = 10000.0) -> None:
        super().__init__(wrapped)
        self.threshold = threshold

    def charge(self, request: ChargeRequest) -> Receipt:
        if request.amount > self.threshold:
            logger.warning(f"[FRAUD] High amount detected: {request.amount}")
            raise FraudDetectedError("Potential fraud detected")
        return super().charge(request)


# --- Audit Decorator ---
class AuditDecorator(ProcessorDecorator):
    def __init__(self, wrapped: PaymentProcessor) -> None:
        super().__init__(wrapped)
        self.audit_log = []

    def charge(self, request: ChargeRequest) -> Receipt:
        start = time.time()
        try:
            receipt = super().charge(request)
            duration = time.time() - start
            self.audit_log.append(
                {
                    "timestamp": start,
                    "customer_id": request.customer_id,
                    "amount": request.amount,
                    "receipt_id": receipt.id,
                    "duration": duration,
                    "status": "success",
                }
            )
            logger.info(f"[AUDIT] Recorded charge for {request.customer_id}")
            return receipt
        except Exception as e:
            duration = time.time() - start
            self.audit_log.append(
                {
                    "timestamp": start,
                    "customer_id": request.customer_id,
                    "amount": request.amount,
                    "error": str(e),
                    "duration": duration,
                    "status": "failure",
                }
            )
            logger.info(f"[AUDIT] Recorded failed charge for {request.customer_id}")
            raise


# --- Rate Limit Decorator ---
class RateLimitDecorator(ProcessorDecorator):
    def __init__(
        self, wrapped: PaymentProcessor, rate_per_sec: float, burst: int
    ) -> None:
        super().__init__(wrapped)
        self.rate_per_sec = rate_per_sec
        self.burst = burst
        self.allowance = burst
        self.last_check = time.time()
        self._lock = threading.Lock()

    def charge(self, request: ChargeRequest) -> Receipt:
        with self._lock:
            current = time.time()
            time_passed = current - self.last_check
            self.last_check = current
            self.allowance += time_passed * self.rate_per_sec
            if self.allowance > self.burst:
                self.allowance = self.burst
            if self.allowance < 1.0:
                logger.warning("[RATE LIMIT] Too many requests, try later.")
                raise RateLimitExceededError("Rate limit exceeded")
            else:
                self.allowance -= 1.0
        return super().charge(request)


# --- Example Composition ---
if __name__ == "__main__":
    processor: PaymentProcessor = AuditDecorator(
        IdempotencyDecorator(
            FraudCheckDecorator(
                RateLimitDecorator(FakeProcessor(), rate_per_sec=1.0, burst=5),
                threshold=5000.0,
            ),
            enforce_key=True,
            ttl_seconds=60.0,
        )
    )

    # Example usage
    req = ChargeRequest(customer_id="cust_123", amount=100.0, idempotency_key="abc123")
    receipt1 = processor.charge(req)
    receipt2 = processor.charge(req)  # Should be same as receipt1 if idempotent

    print("Receipt 1:", receipt1)
    print("Receipt 2:", receipt2)
    assert receipt1 == receipt2
