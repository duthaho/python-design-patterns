import logging
import time
from typing import Optional, Protocol, Sequence

import requests
from requests import Response

# --- Logging setup ---
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())


# --- Client Protocol ---
class Client(Protocol):
    def get(self, url: str) -> Response: ...


# --- Base HTTP Client ---
class SimpleHttpClient:
    def get(self, url: str) -> Response:
        return requests.get(url)


# --- Base Decorator ---
class ClientDecorator(Client):
    def __init__(self, wrapped_client: Client) -> None:
        self._wrapped = wrapped_client

    def get(self, url: str) -> Response:
        return self._wrapped.get(url)


# --- Logging Decorator ---
class LoggingClient(ClientDecorator):
    def __init__(self, wrapped_client: Client, per_attempt: bool = True) -> None:
        super().__init__(wrapped_client)
        self.per_attempt = per_attempt

    def get(self, url: str) -> Response:
        logger.info(f"[LOG] Sending GET request to {url}")
        response = super().get(url)
        logger.info(f"[LOG] Received status {response.status_code} from {url}")
        return response


# --- Retry Decorator ---
class RetryClient(ClientDecorator):
    def __init__(
        self,
        wrapped_client: Client,
        max_attempts: int = 3,
        backoff: float = 0.1,
        retry_statuses: Optional[Sequence[int]] = None,
    ) -> None:
        super().__init__(wrapped_client)
        self.max_attempts = max_attempts
        self.backoff = backoff
        self.retry_statuses = set(retry_statuses or range(500, 600))

    def get(self, url: str) -> Response:
        attempt = 0
        while attempt < self.max_attempts:
            try:
                response = super().get(url)
                if response.status_code not in self.retry_statuses:
                    return response
                logger.warning(
                    f"[RETRY] Status {response.status_code} on attempt {attempt + 1}"
                )
            except requests.RequestException as e:
                logger.warning(f"[RETRY] Exception on attempt {attempt + 1}: {e}")
            attempt += 1
            time.sleep(self.backoff * (2**attempt))  # exponential backoff
        raise Exception(f"Failed to GET {url} after {self.max_attempts} attempts")


# --- Circuit Breaker Decorator ---
class CircuitBreakerClient(ClientDecorator):
    def __init__(
        self,
        wrapped_client: Client,
        failure_rate_threshold: float = 50.0,
        window: int = 10,
        reset_timeout: float = 5.0,
    ) -> None:
        super().__init__(wrapped_client)
        self.failure_rate_threshold = failure_rate_threshold
        self.window = window
        self.reset_timeout = reset_timeout
        self.failures = 0
        self.successes = 0
        self.last_failure_time: Optional[float] = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN

    def get(self, url: str) -> Response:
        if self.state == "OPEN":
            if time.time() - (self.last_failure_time or 0) > self.reset_timeout:
                logger.info("[CB] Moving to HALF_OPEN state")
                self.state = "HALF_OPEN"
            else:
                raise Exception("[CB] Circuit is OPEN. Request blocked.")

        try:
            response = super().get(url)
            if response.status_code >= 500:
                raise requests.RequestException(f"Server error {response.status_code}")
            self._record_success()
            return response
        except requests.RequestException as e:
            self._record_failure()
            raise e

    def _record_success(self) -> None:
        if self.state == "HALF_OPEN":
            logger.info("[CB] Success in HALF_OPEN, closing circuit")
            self.state = "CLOSED"
            self.failures = 0
            self.successes = 0
        else:
            self.successes += 1
        self._check_state()

    def _record_failure(self) -> None:
        self.failures += 1
        self.last_failure_time = time.time()
        self._check_state()

    def _check_state(self) -> None:
        total = self.failures + self.successes
        if total >= self.window:
            failure_rate = (self.failures / total) * 100
            if failure_rate >= self.failure_rate_threshold:
                logger.warning("[CB] Opening circuit due to high failure rate")
                self.state = "OPEN"
                self.failures = 0
                self.successes = 0


# --- Metrics Sink Protocol ---
class MetricsSink(Protocol):
    def record(self, metric: str, value: float) -> None: ...


# --- In-memory Metrics Sink ---
class InMemoryMetrics:
    def __init__(self) -> None:
        self.metrics = {}

    def record(self, metric: str, value: float) -> None:
        self.metrics.setdefault(metric, []).append(value)
        logger.info(f"[METRICS] {metric} = {value}")


# --- Metrics Decorator ---
class MetricsClient(ClientDecorator):
    def __init__(self, wrapped_client: Client, sink: MetricsSink) -> None:
        super().__init__(wrapped_client)
        self.sink = sink

    def get(self, url: str) -> Response:
        start_time = time.time()
        try:
            response = super().get(url)
            latency = time.time() - start_time
            self.sink.record("http_request_latency_seconds", latency)
            self.sink.record("http_response_status", response.status_code)
            return response
        except Exception:
            latency = time.time() - start_time
            self.sink.record("http_request_latency_seconds", latency)
            self.sink.record("http_request_failure", 1)
            raise


# --- Example usage ---
if __name__ == "__main__":
    metrics_sink = InMemoryMetrics()
    base_client = SimpleHttpClient()

    # Recommended order: metrics → retry → logging → circuit breaker → base
    client = MetricsClient(
        RetryClient(
            LoggingClient(CircuitBreakerClient(base_client), per_attempt=True),
            max_attempts=3,
            retry_statuses=[500, 502, 503, 504],
        ),
        sink=metrics_sink,
    )

    try:
        resp = client.get("https://httpbin.org/status/500")
        print("Final status:", resp.status_code)
    except Exception as e:
        print("Request failed:", e)
