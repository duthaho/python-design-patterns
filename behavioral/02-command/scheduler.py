import random
import time
import uuid
from dataclasses import dataclass
from typing import Callable


# ---------- Exceptions ----------
class TransientError(Exception):
    """Raised for retryable errors (e.g., network timeouts)."""

    pass


# ---------- Metadata ----------
@dataclass(frozen=True)
class CommandMeta:
    name: str
    idempotency_key: str
    correlation_id: str
    max_retries: int = 3
    base_backoff: float = 0.5  # seconds


@dataclass
class WrappedCommand:
    meta: CommandMeta
    fn: Callable[[], None]
    attempts: int = 0

    def execute(self) -> None:
        self.fn()


# ---------- Scheduler ----------
class Scheduler:
    def __init__(self):
        self.queue: list[WrappedCommand] = []
        self.logs: list[dict] = []
        self.completed: dict[str, dict] = {}  # idempotency store
        self.metrics: dict[str, int] = {}

    def submit(self, cmd: WrappedCommand) -> None:
        # Idempotency check
        if cmd.meta.idempotency_key in self.completed:
            self.logs.append(
                {
                    "event": "skipped",
                    "name": cmd.meta.name,
                    "correlation_id": cmd.meta.correlation_id,
                    "reason": "idempotent replay",
                }
            )
            return
        self.queue.append(cmd)

    def run(self) -> None:
        while self.queue:
            cmd = self.queue.pop(0)
            try:
                cmd.attempts += 1
                start = time.time()
                self.logs.append(
                    {
                        "event": "start",
                        "name": cmd.meta.name,
                        "correlation_id": cmd.meta.correlation_id,
                        "attempts": cmd.attempts,
                    }
                )

                cmd.execute()

                duration = int((time.time() - start) * 1000)
                self.logs.append(
                    {
                        "event": "success",
                        "name": cmd.meta.name,
                        "correlation_id": cmd.meta.correlation_id,
                        "attempts": cmd.attempts,
                        "duration_ms": duration,
                    }
                )
                # Mark as completed for idempotency
                self.completed[cmd.meta.idempotency_key] = {"status": "done"}
                # Metrics
                self.metrics[cmd.meta.name] = self.metrics.get(cmd.meta.name, 0) + 1

            except TransientError as te:
                self.logs.append(
                    {
                        "event": "retry",
                        "name": cmd.meta.name,
                        "correlation_id": cmd.meta.correlation_id,
                        "attempts": cmd.attempts,
                        "error": str(te),
                    }
                )
                if cmd.attempts < cmd.meta.max_retries:
                    # Exponential backoff with jitter
                    backoff = cmd.meta.base_backoff * (2 ** (cmd.attempts - 1))
                    jitter = random.uniform(0, backoff * 0.1)
                    sleep_time = backoff + jitter
                    time.sleep(sleep_time)
                    self.queue.append(cmd)
                else:
                    self.logs.append(
                        {
                            "event": "failed",
                            "name": cmd.meta.name,
                            "correlation_id": cmd.meta.correlation_id,
                            "attempts": cmd.attempts,
                            "error": str(te),
                        }
                    )
            except Exception as e:
                self.logs.append(
                    {
                        "event": "failed",
                        "name": cmd.meta.name,
                        "correlation_id": cmd.meta.correlation_id,
                        "attempts": cmd.attempts,
                        "error": str(e),
                    }
                )


# ---------- Example remote call ----------
def flaky_remote_call():
    if random.random() < 0.6:  # 60% chance of failure
        raise TransientError("Network timeout")
    print("Remote call OK")


# ---------- Demo ----------
def demo():
    scheduler = Scheduler()
    cmd = WrappedCommand(
        meta=CommandMeta(
            name="NotifyShipment",
            idempotency_key="K1",
            correlation_id=str(uuid.uuid4()),
            max_retries=4,
            base_backoff=0.2,
        ),
        fn=flaky_remote_call,
    )
    scheduler.submit(cmd)
    scheduler.run()

    print("\n--- Logs ---")
    for log in scheduler.logs:
        print(log)

    print("\n--- Metrics ---")
    print(scheduler.metrics)


if __name__ == "__main__":
    demo()
