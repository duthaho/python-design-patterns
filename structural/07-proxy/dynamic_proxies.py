import asyncio
import functools
import inspect
import time
import uuid
from collections import deque
from typing import Any, Callable


def wrap(obj: Any, *layers: Callable[..., Any]) -> Any:
    """Wrap all public callables on obj with the given layers."""
    for attr_name in dir(obj):
        if attr_name.startswith("_"):
            continue
        attr = getattr(obj, attr_name)
        if callable(attr):
            wrapped_fn = attr
            for layer in layers:
                wrapped_fn = layer(wrapped_fn, f"{obj.__class__.__name__}.{attr_name}")
            setattr(obj, attr_name, wrapped_fn)
    return obj


# Example layer: tracing
def tracing_layer(fn: Callable, name: str) -> Callable:
    if inspect.iscoroutinefunction(fn):

        async def _async(*args, **kwargs):
            rid = str(uuid.uuid4())[:8]
            start = time.time()
            print(f"[trace] {rid} -> {name} start")
            try:
                return await fn(*args, **kwargs)
            finally:
                print(f"[trace] {rid} <- {name} end ({(time.time()-start)*1000:.1f}ms)")

        return functools.wraps(fn)(_async)
    else:

        def _sync(*args, **kwargs):
            rid = str(uuid.uuid4())[:8]
            start = time.time()
            print(f"[trace] {rid} -> {name} start")
            try:
                return fn(*args, **kwargs)
            finally:
                print(f"[trace] {rid} <- {name} end ({(time.time()-start)*1000:.1f}ms)")

        return functools.wraps(fn)(_sync)


def rate_limit_layer(calls: int, period_s: float) -> Callable:
    """Allow at most `calls` calls per `period_s` seconds."""

    def decorator(fn: Callable, name: str) -> Callable:
        timestamps = deque()

        def _check_rate_limit():
            now = time.time()
            # Remove timestamps outside the window
            while timestamps and now - timestamps[0] > period_s:
                timestamps.popleft()
            if len(timestamps) >= calls:
                raise RuntimeError(
                    f"[rate-limit] {name} exceeded {calls} calls/{period_s}s"
                )
            timestamps.append(now)

        if inspect.iscoroutinefunction(fn):

            async def _async(*args, **kwargs):
                _check_rate_limit()
                return await fn(*args, **kwargs)

            return functools.wraps(fn)(_async)
        else:

            def _sync(*args, **kwargs):
                _check_rate_limit()
                return fn(*args, **kwargs)

            return functools.wraps(fn)(_sync)

    return decorator


def circuit_breaker_layer(failure_threshold: int, recovery_time_s: float) -> Callable:
    """Open the circuit after `failure_threshold` consecutive failures, recover after `recovery_time_s`."""

    def decorator(fn: Callable, name: str) -> Callable:
        state = {"failures": 0, "opened_at": None}

        def _before_call():
            if state["opened_at"] is not None:
                elapsed = time.time() - state["opened_at"]
                if elapsed < recovery_time_s:
                    raise RuntimeError(
                        f"[circuit-breaker] {name} is OPEN; retry after {recovery_time_s - elapsed:.1f}s"
                    )
                else:
                    print(f"[circuit-breaker] {name} half-open: testing call")

        def _after_success():
            state["failures"] = 0
            state["opened_at"] = None

        def _after_failure():
            state["failures"] += 1
            if state["failures"] >= failure_threshold:
                state["opened_at"] = time.time()
                print(
                    f"[circuit-breaker] {name} OPENED after {state['failures']} failures"
                )

        if inspect.iscoroutinefunction(fn):

            async def _async(*args, **kwargs):
                _before_call()
                try:
                    result = await fn(*args, **kwargs)
                except Exception:
                    _after_failure()
                    raise
                else:
                    _after_success()
                    return result

            return functools.wraps(fn)(_async)
        else:

            def _sync(*args, **kwargs):
                _before_call()
                try:
                    result = fn(*args, **kwargs)
                except Exception:
                    _after_failure()
                    raise
                else:
                    _after_success()
                    return result

            return functools.wraps(fn)(_sync)

    return decorator


class DemoService:
    def compute(self, x: int) -> int:
        time.sleep(0.05)
        if x % 7 == 0:
            raise RuntimeError("boom")
        return x * x

    async def fetch(self, x: int) -> int:
        await asyncio.sleep(0.05)
        return x + 1


if __name__ == "__main__":
    svc = DemoService()
    svc = wrap(
        svc,
        tracing_layer,
        rate_limit_layer(calls=5, period_s=1),
        circuit_breaker_layer(failure_threshold=3, recovery_time_s=5),
    )

    # Sync calls
    for i in range(1, 12):
        try:
            print("compute:", svc.compute(i))
        except Exception as e:
            print("compute error:", e)

    # Async calls
    async def main():
        try:
            print("fetch:", await svc.fetch(1))
        except Exception as e:
            print("fetch error:", e)

    asyncio.run(main())
