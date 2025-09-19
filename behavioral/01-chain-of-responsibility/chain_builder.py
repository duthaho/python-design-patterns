import time
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Type

# ---------------- Tracing ---------------- #


class Tracer:
    def on_enter(self, name: str, req: Any):
        print(f"[enter] {name} req={getattr(req, 'path', None) or req}")

    def on_exit(self, name: str, req: Any, res: Any, error: Exception | None = None):
        state = "error" if error else "ok"
        print(f"[exit]  {name} state={state} res={res}")


# ---------------- Request Model ---------------- #


class Request:
    def __init__(self, path: str, attrs: Dict[str, Any] | None = None):
        self.path = path
        self.attrs = attrs or {}


# ---------------- Handler Base ---------------- #


class Handler(ABC):
    def __init__(self, tracer: Tracer | None = None):
        self._next: Optional["Handler"] = None
        self.tracer = tracer

    def set_next(self, h: "Handler") -> "Handler":
        self._next = h
        return h

    def _forward(self, req: Request):
        if self._next:
            return self._next.handle(req)
        return {"status": "ok", "attrs": req.attrs}

    def handle(self, req: Request):
        name = self.__class__.__name__
        if self.tracer:
            self.tracer.on_enter(name, req)
        try:
            res = self._handle(req)
            if self.tracer:
                self.tracer.on_exit(name, req, res, None)
            return res
        except Exception as e:
            if self.tracer:
                self.tracer.on_exit(name, req, None, e)
            raise

    @abstractmethod
    def _handle(self, req: Request): ...


# ---------------- Example Handlers ---------------- #


class RateLimiter(Handler):
    def __init__(self, limit: int, window_sec: int, tracer: Tracer | None = None):
        super().__init__(tracer)
        self.limit = limit
        self.window_sec = window_sec
        self.rate_limit_state: Dict[tuple, list[float]] = {}

    def _handle(self, req: Request):
        now = time.time()
        window_start = now - self.window_sec
        key = (req.attrs.get("client_id", "anon"), req.path)
        timestamps = [t for t in self.rate_limit_state.get(key, []) if t > window_start]
        if len(timestamps) >= self.limit:
            return {"status": "rate_limited", "attrs": req.attrs}
        timestamps.append(now)
        self.rate_limit_state[key] = timestamps
        return self._forward(req)


class CircuitBreaker(Handler):
    def __init__(self, failure_threshold: int, tracer: Tracer | None = None):
        super().__init__(tracer)
        self.failure_threshold = failure_threshold
        self.failure_count = 0
        self.state = "closed"

    def _handle(self, req: Request):
        if self.state == "open":
            return {"status": "circuit_open", "attrs": req.attrs}

        res = self._forward(req)

        if res.get("status") != "ok":
            self.failure_count += 1
            if self.failure_count >= self.failure_threshold:
                self.state = "open"
        else:
            self.failure_count = 0
            self.state = "closed"

        return res


class Router(Handler):
    def __init__(self, routes: Dict[str, Handler], tracer: Tracer | None = None):
        super().__init__(tracer)
        self.routes = routes

    def _handle(self, req: Request):
        # Attribute-based routing
        if "route" in req.attrs and req.attrs["route"] in self.routes:
            return self.routes[req.attrs["route"]].handle(req)

        # Prefix-based routing
        for prefix, handler in self.routes.items():
            if req.path.startswith(prefix):
                return handler.handle(req)

        # Default route
        if "default" in self.routes:
            return self.routes["default"].handle(req)

        return {"status": "no_route", "attrs": req.attrs}


class HandlerA(Handler):
    def __init__(self, feature_flag: bool = False, tracer: Tracer | None = None):
        super().__init__(tracer)
        self.feature_flag = feature_flag

    def _handle(self, req: Request):
        if self.feature_flag:
            req.attrs["feature"] = "enabled"
        return self._forward(req)


class HandlerB(Handler):
    def __init__(self, fail: bool = False, tracer: Tracer | None = None):
        super().__init__(tracer)
        self.fail = fail

    def _handle(self, req: Request):
        req.attrs["processed_by"] = "HandlerB"
        if self.fail:
            return {"status": "error", "attrs": req.attrs}
        return self._forward(req)


# ---------------- Chain Builder ---------------- #


class ChainBuilder:
    def __init__(self, tracer: Tracer | None = None):
        self.tracer = tracer
        self.registry: Dict[str, Type[Handler]] = {}

    def register(self, name: str, cls: Type[Handler]):
        self.registry[name] = cls

    def build(self, config: list[dict]) -> Handler:
        if not config:
            raise ValueError("Empty config")

        first_handler = None
        prev_handler = None

        for entry in config:
            h_type = entry["type"]
            params = entry.get("params", {})
            cls = self.registry.get(h_type)
            if not cls:
                raise ValueError(f"Handler type '{h_type}' not registered")

            if "tracer" in cls.__init__.__code__.co_varnames:
                params["tracer"] = self.tracer

            handler = cls(**params)

            if not first_handler:
                first_handler = handler
            if prev_handler:
                prev_handler.set_next(handler)
            prev_handler = handler

        return first_handler


# ---------------- Demo ---------------- #

if __name__ == "__main__":
    tracer = Tracer()
    builder = ChainBuilder(tracer)

    # Register handlers
    builder.register("RateLimiter", RateLimiter)
    builder.register("CircuitBreaker", CircuitBreaker)
    builder.register("Router", Router)
    builder.register("HandlerA", HandlerA)
    builder.register("HandlerB", HandlerB)

    # Build subchains for Router
    sub_a = builder.build(
        [{"type": "HandlerA", "params": {"feature_flag": True}}, {"type": "HandlerB"}]
    )
    sub_b = builder.build(
        [{"type": "HandlerB", "params": {"fail": True}}]  # Simulate failure
    )

    router = Router(routes={"/a": sub_a, "/b": sub_b, "default": sub_a}, tracer=tracer)

    # Top-level chain
    rate_limiter = RateLimiter(limit=3, window_sec=10, tracer=tracer)
    breaker = CircuitBreaker(failure_threshold=2, tracer=tracer)
    rate_limiter.set_next(breaker).set_next(router)

    # Test requests
    test_requests = [
        Request("/a", {"client_id": "u1"}),
        Request("/a", {"client_id": "u1"}),
        Request("/b", {"client_id": "u1"}),  # Will fail
        Request("/b", {"client_id": "u1"}),  # Will fail again -> breaker opens
        Request("/a", {"client_id": "u1"}),  # Breaker now open
        Request("/c", {"client_id": "u1"}),  # Default route
    ]

    for r in test_requests:
        print("Result:", rate_limiter.handle(r), end="\n\n")
