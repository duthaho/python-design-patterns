from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Any, Optional, Self
import copy, threading, uuid


@dataclass(frozen=True)
class RetryPolicy:
    max_retries: int
    backoff_strategy: str  # "exponential" | "linear"
    jitter: bool = True


class Prototype(ABC):
    @abstractmethod
    def clone(self) -> Self: ...

    @abstractmethod
    def describe(self) -> str: ...


class RequestContext(Prototype):
    def __init__(
        self,
        headers: Dict[str, str],
        retry_policy: RetryPolicy,
        timeout_ms: int,
        trace: Dict[str, Any],
        session: Optional[object] = None,
    ):
        self.headers = headers
        self.retry_policy = retry_policy
        self.timeout_ms = timeout_ms
        self.trace = trace
        self.session = session

    def clone(self):
        # TODO: deep copy headers & trace; retain retry_policy as-is (immutable) or deep-copy if you prefer
        # Reset session; generate new span_id
        cloned_headers = copy.deepcopy(self.headers)
        cloned_trace = copy.deepcopy(self.trace)
        cloned_trace["span_id"] = str(uuid.uuid4())

        return RequestContext(
            headers=cloned_headers,
            retry_policy=self.retry_policy,
            timeout_ms=self.timeout_ms,
            trace=cloned_trace,
            session=None,
        )

    def describe(self):
        return f"RequestContext(timeout_ms={self.timeout_ms}, headers={self.headers}, trace={self.trace})"


class ContextBlueprints:
    def __init__(self):
        self._reg: Dict[str, RequestContext] = {}
        self._lock = threading.RLock()

    def register(self, service: str, ctx: RequestContext):
        # TODO: validate and store
        with self._lock:
            if service in self._reg:
                raise ValueError(f"Service '{service}' is already registered.")
            self._reg[service] = ctx

    def get(self, service: str, **overrides) -> RequestContext:
        # TODO: clone and apply overrides with validation (headers lowercased; timeout bounds)
        with self._lock:
            if service not in self._reg:
                raise KeyError(f"Service '{service}' is not registered.")
            prototype = self._reg[service]
            cloned = prototype.clone()
            if "headers" in overrides:
                # Merge headers, ensuring keys are lowercased
                new_headers = {k.lower(): v for k, v in overrides["headers"].items()}
                cloned.headers.update(new_headers)
            if "timeout_ms" in overrides:
                timeout = overrides["timeout_ms"]
                if not (100 <= timeout <= 10000):
                    raise ValueError("timeout_ms must be between 100 and 10000 ms.")
                cloned.timeout_ms = timeout
            return cloned

    def list_services(self) -> tuple[str, ...]:
        with self._lock:
            return tuple(self._reg.keys())


# Integration test skeleton
def simulate_concurrency():
    bp = ContextBlueprints()
    payments_proto = RequestContext(
        headers={"content-type": "application/json", "x-client": "gateway"},
        retry_policy=RetryPolicy(3, "exponential", True),
        timeout_ms=1500,
        trace={"trace_id": str(uuid.uuid4()), "span_id": "init"},
    )
    search_proto = RequestContext(
        headers={"content-type": "application/json", "x-client": "gateway"},
        retry_policy=RetryPolicy(2, "linear", False),
        timeout_ms=800,
        trace={"trace_id": str(uuid.uuid4()), "span_id": "init"},
    )
    bp.register("payments", payments_proto)
    bp.register("search", search_proto)

    results = []
    lock = threading.Lock()

    def worker(service, user_id):
        ctx = bp.get(service, headers={"x-user-id": str(user_id)})
        # simulate request using ctx
        with lock:
            results.append((service, ctx.trace["span_id"], ctx.headers))

    threads = [
        threading.Thread(
            target=worker, args=("payments" if i % 2 == 0 else "search", i)
        )
        for i in range(100)
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(results) == 100

    # TODO: assert no shared headers dict ids across results within the same service batch
    # TODO: spot-check span_id uniqueness
    payments_spans = {span for svc, span, hdr_id in results if svc == "payments"}
    search_spans = {span for svc, span, hdr_id in results if svc == "search"}
    assert len(payments_spans) == 50
    assert len(search_spans) == 50

    payments_header_ids = {
        id(hdr_id) for svc, span, hdr_id in results if svc == "payments"
    }
    search_header_ids = {id(hdr_id) for svc, span, hdr_id in results if svc == "search"}
    assert len(payments_header_ids) == 50
    assert len(search_header_ids) == 50

    print("All tests passed.")


if __name__ == "__main__":
    simulate_concurrency()
