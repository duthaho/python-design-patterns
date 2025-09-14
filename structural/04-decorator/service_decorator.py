import logging
from typing import Any, Callable, Dict, Protocol

# --- Logging setup ---
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())


# --- Example Protocol (replace with your domain interface) ---
class Service(Protocol):
    def do_work(self, data: Any) -> Any: ...


# --- Base Implementation ---
class BaseService:
    def do_work(self, data: Any) -> Any:
        logger.info(f"[BASE] Processing data: {data}")
        return {"processed": data}


# --- Base Decorator ---
class ServiceDecorator(Service):
    def __init__(self, wrapped: Service) -> None:
        self._wrapped = wrapped

    def do_work(self, data: Any) -> Any:
        return self._wrapped.do_work(data)


# --- Example Decorators ---
class LoggingDecorator(ServiceDecorator):
    def do_work(self, data: Any) -> Any:
        logger.info(f"[LOG] Input: {data}")
        result = super().do_work(data)
        logger.info(f"[LOG] Output: {result}")
        return result


class RetryDecorator(ServiceDecorator):
    def __init__(self, wrapped: Service, max_attempts: int = 3) -> None:
        super().__init__(wrapped)
        self.max_attempts = max_attempts

    def do_work(self, data: Any) -> Any:
        for attempt in range(1, self.max_attempts + 1):
            try:
                return super().do_work(data)
            except Exception as e:
                logger.warning(f"[RETRY] Attempt {attempt} failed: {e}")
                if attempt == self.max_attempts:
                    raise


class MetricsDecorator(ServiceDecorator):
    def __init__(self, wrapped: Service, sink: Callable[[str, float], None]) -> None:
        super().__init__(wrapped)
        self.sink = sink

    def do_work(self, data: Any) -> Any:
        import time

        start = time.time()
        try:
            result = super().do_work(data)
            self.sink("service_success", 1)
            return result
        finally:
            duration = time.time() - start
            self.sink("service_latency_seconds", duration)


# --- Metrics Sink Example ---
def in_memory_sink(metric: str, value: float) -> None:
    logger.info(f"[METRICS] {metric} = {value}")


# --- Decorator Registry ---
DECORATOR_REGISTRY: Dict[str, Callable[..., Service]] = {
    "logging": LoggingDecorator,
    "retry": RetryDecorator,
    "metrics": MetricsDecorator,
}


# --- Builder Function ---
def build_service(cfg: Dict[str, Any]) -> Service:
    """
    cfg example:
    {
        "base": "base_service",
        "decorators": [
            {"name": "metrics", "sink": in_memory_sink},
            {"name": "logging"},
            {"name": "retry", "max_attempts": 2}
        ]
    }
    """
    # Step 1: Create base
    if cfg["base"] == "base_service":
        service: Service = BaseService()
    else:
        raise ValueError(f"Unknown base service: {cfg['base']}")

    # Step 2: Apply decorators in order
    for deco_cfg in cfg.get("decorators", []):
        name = deco_cfg.pop("name")
        if name not in DECORATOR_REGISTRY:
            raise ValueError(f"Unknown decorator: {name}")
        decorator_cls = DECORATOR_REGISTRY[name]
        service = decorator_cls(service, **deco_cfg)  # type: ignore
    return service


# --- Example Usage ---
if __name__ == "__main__":
    config = {
        "base": "base_service",
        "decorators": [
            {"name": "metrics", "sink": in_memory_sink},
            {"name": "logging"},
            {"name": "retry", "max_attempts": 2},
        ],
    }

    svc = build_service(config)
    result = svc.do_work({"foo": "bar"})
    print("Final result:", result)
