import threading
import queue
import time
import json
import logging
import random
import os
from typing import Any, Dict


# --- Singleton Metaclass ---
class SingletonMeta(type):
    _instances = {}
    _lock = threading.Lock()

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            with cls._lock:
                if cls not in cls._instances:
                    cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]


# --- LogBus Singleton ---
class LogBus(metaclass=SingletonMeta):
    def __init__(
        self, path: str = "app.log", maxsize: int = 1000, policy: str = "drop_new"
    ) -> None:
        """
        :param path: Path to the log file
        :param maxsize: Max queue size before applying backpressure policy
        :param policy: 'drop_new', 'drop_old', or 'block'
        """
        self.path = path
        self.maxsize = maxsize
        self.policy = policy
        self.queue = queue.Queue(maxsize=maxsize)
        self._stop_event = threading.Event()
        self._lock = threading.Lock()

        # TODO: Initialize file handler or logging handler here
        self._file_handler = open(self.path, "a")

        # TODO: Start worker thread
        self._worker_thread = threading.Thread(target=self._worker, daemon=True)
        self._worker_thread.start()

    def _worker(self) -> None:
        """Background thread that drains the queue and writes logs."""
        while not self._stop_event.is_set() or not self.queue.empty():
            try:
                event = self.queue.get(timeout=0.5)
                self._write_event(event)
                self.queue.task_done()
            except queue.Empty:
                continue

    def _write_event(self, event: Dict[str, Any]) -> None:
        """Write a single event to the log file."""
        # TODO: Implement structured logging (e.g., JSON lines)
        self._file_handler.write(json.dumps(event) + "\n")
        self._file_handler.flush()

    def emit(self, event: Dict[str, Any]) -> bool:
        """
        Add an event to the queue according to the backpressure policy.
        :param event: A dictionary representing the log event
        """
        # TODO: Implement policy handling:
        # - drop_new: discard if full
        # - drop_old: remove oldest and enqueue new
        # - block: wait until space is available
        try:
            if self.policy == "drop_new":
                self.queue.put(event, block=False)
                return True
            elif self.policy == "drop_old":
                dropped = False
                if self.queue.full():
                    try:
                        self.queue.get_nowait()  # Remove oldest
                        dropped = True
                    except queue.Empty:
                        pass
                self.queue.put(event, block=False)
                return not dropped  # False if we had to drop something
            elif self.policy == "block":
                self.queue.put(event, block=True)
                return True
            else:
                raise ValueError(f"Unknown policy: {self.policy}")
        except queue.Full:
            return False

    def close(self, timeout: float = 5.0) -> None:
        """
        Gracefully stop the worker and flush remaining logs.
        :param timeout: Time to wait for flush before forcing exit
        """
        # TODO: Signal stop, join worker, close file handler
        self._stop_event.set()
        self._worker_thread.join(timeout=timeout)
        if self._worker_thread.is_alive():
            logging.warning("LogBus worker thread did not terminate in time.")
            # Optionally drain remaining events synchronously
            while not self.queue.empty():
                try:
                    event = self.queue.get_nowait()
                    self._write_event(event)
                except queue.Empty:
                    break
        self._file_handler.close()


# --- Example usage ---
NUM_THREADS = 10
EVENTS_PER_THREAD = 500
POLICY = "drop_new"  # try "drop_old" or "block"
LOG_PATH = "test.log"

accepted_count = 0
accepted_lock = threading.Lock()


def producer(thread_id: int):
    global accepted_count
    for i in range(EVENTS_PER_THREAD):
        event = {"thread": thread_id, "seq": i, "timestamp": time.time()}
        before = time.time()
        result = logbus.emit(event)
        after = time.time()

        if result:
            with accepted_lock:
                accepted_count += 1

        time.sleep(random.uniform(0, 0.002))

        if POLICY == "block" and (after - before) > 0.05:
            print(f"[Thread {thread_id}] emit() blocked for {after - before:.3f}s")


def parse_and_verify_log(path: str):
    """Parse the log file and verify JSON integrity, uniqueness, and ordering."""
    if not os.path.exists(path):
        print(f"Log file {path} not found.")
        return

    seen_keys = set()
    events = []

    with open(path, "r") as f:
        for lineno, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError as e:
                print(f"❌ JSON decode error on line {lineno}: {e}")
                continue

            # Check required keys
            if not all(k in event for k in ("thread", "seq", "timestamp")):
                print(f"❌ Missing keys in event on line {lineno}: {event}")
                continue

            key = (event["thread"], event["seq"])
            if key in seen_keys:
                print(f"❌ Duplicate event detected: {key}")
            seen_keys.add(key)

            events.append(event)

    print(f"✅ Parsed {len(events)} valid events from log.")

    # Optional: Check ordering by timestamp
    timestamps = [e["timestamp"] for e in events]
    if timestamps != sorted(timestamps):
        print(
            "⚠️ Warning: Events are not strictly in timestamp order (may be expected with concurrency)."
        )
    else:
        print("✅ Events are in non-decreasing timestamp order.")


if __name__ == "__main__":
    # Clean up old log
    if os.path.exists(LOG_PATH):
        os.remove(LOG_PATH)

    logbus = LogBus(path=LOG_PATH, maxsize=100, policy=POLICY)

    threads = [
        threading.Thread(target=producer, args=(tid,)) for tid in range(NUM_THREADS)
    ]

    start_time = time.time()
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    logbus.close()

    elapsed = time.time() - start_time
    print(f"Test finished in {elapsed:.2f}s")
    print(f"Total events attempted: {NUM_THREADS * EVENTS_PER_THREAD}")
    print(f"Total events accepted: {accepted_count}")
    print(f"Acceptance ratio: {accepted_count / (NUM_THREADS * EVENTS_PER_THREAD):.2%}")

    # Parse and verify log file
    parse_and_verify_log(LOG_PATH)
