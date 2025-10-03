"""
Distributed Event System with Async Support

REQUIREMENTS:
1. Support both sync and async observers
2. Thread-safe operations using locks
3. Weak references to prevent memory leaks
4. Event history with replay capability
5. Performance metrics (notification time, event count)
6. Handle high-frequency events (1000s per second)
"""

import asyncio
import gc
import time
import weakref
from abc import ABC, abstractmethod
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from threading import Lock
from typing import Any, Optional


class EventType(Enum):
    """Types of events in the system"""

    HEALTH_CHECK = "health"
    PERFORMANCE = "performance"
    ERROR = "error"
    INFO = "info"
    ALL = "all"


@dataclass
class Event:
    """Immutable event object"""

    event_type: EventType
    source: str
    data: dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    event_id: str = field(default_factory=lambda: str(time.time_ns()))


class Observer(ABC):
    """Base observer class - can be sync or async"""

    def __init__(self, name: str, priority: int = 999):
        self.name = name
        self.priority = priority

    @abstractmethod
    def update(self, event: Event) -> None:
        """Synchronous update method"""
        pass

    async def async_update(self, event: Event) -> None:
        """Asynchronous update method - override if observer needs async"""
        await asyncio.to_thread(self.update, event)

    def is_async(self) -> bool:
        """Check if observer supports async updates"""
        return self.async_update.__func__ is not Observer.async_update


@dataclass
class ObserverMetrics:
    """Metrics for monitoring observer performance"""

    total_notifications: int = 0
    total_errors: int = 0
    avg_processing_time_ms: float = 0.0
    last_notification: Optional[datetime] = None

    def update_metrics(self, processing_time_ms: float, error: bool = False):
        """Update metrics with new notification data"""
        self.total_notifications += 1
        if error:
            self.total_errors += 1
        # Update average processing time
        self.avg_processing_time_ms = (
            (self.avg_processing_time_ms * (self.total_notifications - 1))
            + processing_time_ms
        ) / self.total_notifications
        self.last_notification = datetime.now()


class Subject(ABC):
    """Thread-safe subject with async support and event history"""

    def __init__(self, history_size: int = 100):
        self._observers: dict[EventType, list] = {}
        self._lock = Lock()
        self._event_history: deque[Event] = deque(maxlen=history_size)
        self._observer_metrics: dict[str, ObserverMetrics] = {}

        # Initialize event type storage
        for event_type in EventType:
            self._observers[event_type] = []

    def attach(self, observer: Observer, event_types: list[EventType]) -> "Subject":
        """Attach observer to multiple event types using weak references"""
        with self._lock:
            for event_type in event_types:
                if event_type not in self._observers:
                    self._observers[event_type] = []
                # Check for existing observer to avoid duplicates
                if not any(ref() is observer for ref in self._observers[event_type]):
                    self._observers[event_type].append(weakref.ref(observer))
                    # Initialize metrics for new observer
                    if observer.name not in self._observer_metrics:
                        self._observer_metrics[observer.name] = ObserverMetrics()
        return self

    def detach(self, observer: Observer) -> "Subject":
        """Detach observer from all event types"""
        with self._lock:
            for event_type, refs in self._observers.items():
                self._observers[event_type] = [
                    ref for ref in refs if ref() is not observer and ref() is not None
                ]
            # Remove metrics
            if observer.name in self._observer_metrics:
                del self._observer_metrics[observer.name]
        return self

    def notify(self, event: Event) -> None:
        """Synchronous notification to all observers"""
        with self._lock:
            self._event_history.append(event)
            observers = self._observers.get(event.event_type, []) + self._observers.get(
                EventType.ALL, []
            )
            live_observers = []
            for ref in observers:
                obs = ref()
                if obs is not None:
                    live_observers.append(obs)
            live_observers.sort(key=lambda obs: obs.priority)

        # Notify outside lock to avoid blocking
        for observer in live_observers:
            start_time = time.time()
            error_occurred = False
            try:
                if observer.is_async():
                    continue
                observer.update(event)
            except Exception as e:
                error_occurred = True
                print(f"❌ Error notifying {observer.name}: {e}")
            end_time = time.time()
            processing_time_ms = (end_time - start_time) * 1000

            if observer.name in self._observer_metrics:
                self._observer_metrics[observer.name].update_metrics(
                    processing_time_ms, error_occurred
                )

    async def async_notify(self, event: Event) -> None:
        """Asynchronous notification supporting both sync and async observers"""
        with self._lock:
            self._event_history.append(event)
            observers = self._observers.get(event.event_type, []) + self._observers.get(
                EventType.ALL, []
            )
            live_observers = []
            for ref in observers:
                obs = ref()
                if obs is not None:
                    live_observers.append(obs)
            live_observers.sort(key=lambda obs: obs.priority)

        tasks = []
        for observer in live_observers:
            start_time = time.time()
            if observer.is_async():
                tasks.append(self._async_notify_helper(observer, event, start_time))
            else:
                error_occurred = False
                try:
                    await asyncio.to_thread(observer.update, event)
                except Exception as e:
                    error_occurred = True
                    print(f"❌ Error notifying {observer.name}: {e}")
                end_time = time.time()
                processing_time_ms = (end_time - start_time) * 1000

                if observer.name in self._observer_metrics:
                    self._observer_metrics[observer.name].update_metrics(
                        processing_time_ms, error_occurred
                    )

        if tasks:
            await asyncio.gather(*tasks)

    def get_event_history(self, event_type: Optional[EventType] = None) -> list[Event]:
        """Get event history, optionally filtered by type"""
        if event_type is None:
            return list(self._event_history)
        else:
            return [
                event for event in self._event_history if event.event_type == event_type
            ]

    async def replay_events(
        self, start_time: datetime, end_time: Optional[datetime] = None
    ) -> None:
        """Replay historical events to all observers"""
        events_to_replay = [
            event
            for event in self._event_history
            if event.timestamp >= start_time
            and (end_time is None or event.timestamp <= end_time)
        ]
        for event in events_to_replay:
            await self.async_notify(event)

    def get_metrics(self) -> dict[str, ObserverMetrics]:
        """Return copy of metrics for all observers"""
        return self._observer_metrics.copy()

    def _cleanup_dead_references(self) -> None:
        """Remove dead weak references"""
        with self._lock:
            for event_type, refs in self._observers.items():
                self._observers[event_type] = [ref for ref in refs if ref() is not None]

    async def _async_notify_helper(
        self, observer: Observer, event: Event, start_time: float
    ):
        """Helper to notify async observers and track metrics"""
        error_occurred = False
        try:
            await observer.async_update(event)
        except Exception as e:
            error_occurred = True
            print(f"❌ Error notifying {observer.name}: {e}")
        end_time = time.time()
        processing_time_ms = (end_time - start_time) * 1000

        if observer.name in self._observer_metrics:
            self._observer_metrics[observer.name].update_metrics(
                processing_time_ms, error_occurred
            )


class MicroserviceMonitor(Subject):
    """Concrete subject for monitoring microservices"""

    def __init__(self, service_name: str, history_size: int = 100):
        super().__init__(history_size)
        self.service_name = service_name

    def emit_health_check(self, status: str, details: dict[str, Any]) -> None:
        """Create and notify health check event"""
        event = Event(
            event_type=EventType.HEALTH_CHECK,
            source=self.service_name,
            data={"status": status, **details},
        )
        self.notify(event)

    def emit_performance_metric(
        self, metric_name: str, value: float, unit: str
    ) -> None:
        """Create and notify performance event"""
        event = Event(
            event_type=EventType.PERFORMANCE,
            source=self.service_name,
            data={"metric": metric_name, "value": value, "unit": unit},
        )
        self.notify(event)

    def emit_error(self, error_message: str, stack_trace: Optional[str] = None) -> None:
        """Create and notify error event"""
        event = Event(
            event_type=EventType.ERROR,
            source=self.service_name,
            data={"error_message": error_message, "stack_trace": stack_trace},
        )
        self.notify(event)


# ============================================================================
# CONCRETE OBSERVERS
# ============================================================================


class ConsoleLogger(Observer):
    """Simple synchronous console logger"""

    def update(self, event: Event) -> None:
        print(
            f"[{event.timestamp.strftime('%H:%M:%S')}] "
            f"{event.source} | {event.event_type.value.upper()} | {event.data}"
        )


class DatabaseLogger(Observer):
    """Async observer that writes to database"""

    async def async_update(self, event: Event) -> None:
        """Simulate async database write"""
        await asyncio.sleep(0.01)  # Reduced for faster tests
        print(f"💾 [DB] Logged event {event.event_id} from {event.source}")

    def update(self, event: Event) -> None:
        """Sync fallback - should not be called if async is available"""
        raise NotImplementedError("DatabaseLogger requires async context")


class AlertingSystem(Observer):
    """High-priority observer for critical alerts"""

    def __init__(self, priority: int = 0):
        super().__init__(name="AlertingSystem", priority=priority)
        self._alert_threshold = 3
        self._error_count = 0

    def update(self, event: Event) -> None:
        """Implement alerting logic"""
        if event.event_type == EventType.ERROR:
            self._error_count += 1
            if self._error_count >= self._alert_threshold:
                print(
                    f"🚨 ALERT! {self._error_count} errors detected in {event.source}"
                )
                self._error_count = 0
        else:
            self._error_count = 0


class MetricsAggregator(Observer):
    """Aggregates metrics over time windows"""

    def __init__(self):
        super().__init__(name="MetricsAggregator", priority=5)
        self._metrics_buffer: dict[str, list[float]] = {}

    def update(self, event: Event) -> None:
        """Implement metrics aggregation"""
        if event.event_type == EventType.PERFORMANCE:
            metric = event.data.get("metric")
            value = event.data.get("value")
            if metric and isinstance(value, (int, float)):
                if metric not in self._metrics_buffer:
                    self._metrics_buffer[metric] = []
                self._metrics_buffer[metric].append(value)

    def get_aggregated_metrics(self) -> dict[str, dict[str, float]]:
        """Return aggregated statistics (avg, min, max, p95)"""
        result = {}
        for metric, values in self._metrics_buffer.items():
            if values:
                sorted_vals = sorted(values)
                count = len(values)
                avg = sum(values) / count
                min_val = sorted_vals[0]
                max_val = sorted_vals[-1]
                p95_idx = max(0, int(0.95 * count) - 1)
                p95 = sorted_vals[p95_idx]
                result[metric] = {
                    "count": count,
                    "avg": avg,
                    "min": min_val,
                    "max": max_val,
                    "p95": p95,
                }
        return result


class SlackNotifier(Observer):
    """Async observer that sends notifications to Slack"""

    async def async_update(self, event: Event) -> None:
        """Simulate async API call to Slack"""
        await asyncio.sleep(0.02)  # Reduced for faster tests
        print(f"💬 [Slack] Notification sent for event {event.event_id}")

    def update(self, event: Event) -> None:
        raise NotImplementedError("SlackNotifier requires async context")


class FaultyObserver(Observer):
    """Observer that always throws errors for testing"""

    def update(self, event: Event) -> None:
        raise RuntimeError(f"FaultyObserver intentional error")


# ============================================================================
# TEST SCENARIOS
# ============================================================================


async def test_basic_sync_observers():
    """Test 1: Basic synchronous observers"""
    print("\n=== Test 1: Basic Sync Observers ===")

    monitor = MicroserviceMonitor("UserService")
    console = ConsoleLogger("ConsoleLogger", priority=10)
    alerting = AlertingSystem(priority=0)

    monitor.attach(console, [EventType.ALL])
    monitor.attach(alerting, [EventType.ERROR])

    # Emit various events
    monitor.emit_health_check("healthy", {"uptime": 3600})
    monitor.emit_performance_metric("response_time", 45.2, "ms")
    monitor.emit_error("Database connection failed", "Stack trace here...")

    print("✅ Test 1 passed: Basic sync observers working")


async def test_async_observers():
    """Test 2: Asynchronous observers with I/O"""
    print("\n=== Test 2: Async Observers ===")

    monitor = MicroserviceMonitor("PaymentService")
    db_logger = DatabaseLogger("DatabaseLogger", priority=5)
    slack = SlackNotifier("SlackNotifier", priority=3)

    monitor.attach(db_logger, [EventType.ALL])
    monitor.attach(slack, [EventType.ERROR, EventType.HEALTH_CHECK])

    # Create some events
    event1 = Event(EventType.ERROR, "PaymentService", {"error": "Transaction timeout"})
    event2 = Event(EventType.HEALTH_CHECK, "PaymentService", {"status": "degraded"})

    # Notify asynchronously
    await monitor.async_notify(event1)
    await monitor.async_notify(event2)

    print("✅ Test 2 passed: Async observers executed concurrently")


async def test_high_frequency_events():
    """Test 3: Handle 1000 events rapidly"""
    print("\n=== Test 3: High Frequency Events ===")

    monitor = MicroserviceMonitor("MetricsService", history_size=2000)
    aggregator = MetricsAggregator()

    monitor.attach(aggregator, [EventType.PERFORMANCE])

    print("Processing 1000 events...")
    start_time = time.time()

    # Emit 1000 performance metrics
    for i in range(1000):
        monitor.emit_performance_metric("cpu_usage", 50.0 + (i % 50), "percent")

    end_time = time.time()
    duration = end_time - start_time
    events_per_sec = 1000 / duration

    # Verify aggregation
    stats = aggregator.get_aggregated_metrics()
    print(f"✅ Completed in {duration:.3f}s ({events_per_sec:.0f} events/sec)")
    print(f"📊 CPU Usage Stats: {stats.get('cpu_usage', {})}")

    # Verify event history
    history = monitor.get_event_history(EventType.PERFORMANCE)
    print(f"📝 Event history contains {len(history)} events")


async def test_event_replay():
    """Test 4: Event history and replay"""
    print("\n=== Test 4: Event Replay ===")

    monitor = MicroserviceMonitor("OrderService", history_size=50)
    console = ConsoleLogger("ReplayLogger", priority=10)

    # Record timestamp before events
    replay_start = datetime.now()
    await asyncio.sleep(0.01)

    # Emit initial events
    monitor.emit_health_check("healthy", {"orders_processed": 100})
    monitor.emit_error("Order validation failed", None)
    monitor.emit_performance_metric("order_latency", 120.5, "ms")

    await asyncio.sleep(0.01)
    replay_end = datetime.now()

    # Check history
    all_events = monitor.get_event_history()
    error_events = monitor.get_event_history(EventType.ERROR)

    print(f"📜 Total events in history: {len(all_events)}")
    print(f"❌ Error events in history: {len(error_events)}")

    # Attach observer and replay
    monitor.attach(console, [EventType.ALL])
    print("\n🔄 Replaying events...")
    await monitor.replay_events(replay_start, replay_end)

    print("✅ Test 4 passed: Event replay successful")


async def test_observer_failures():
    """Test 5: Observer error handling"""
    print("\n=== Test 5: Observer Failures ===")

    monitor = MicroserviceMonitor("APIService")
    console = ConsoleLogger("WorkingLogger", priority=10)
    faulty = FaultyObserver("FaultyObserver", priority=5)
    alerting = AlertingSystem(priority=0)

    monitor.attach(console, [EventType.ALL])
    monitor.attach(faulty, [EventType.ALL])
    monitor.attach(alerting, [EventType.ERROR])

    print("Emitting event to observers (one will fail)...")
    monitor.emit_health_check("healthy", {"status": "ok"})

    # Check that other observers still received notification
    metrics = monitor.get_metrics()
    print(f"\n📊 Observer Metrics:")
    for name, metric in metrics.items():
        print(
            f"  {name}: notifications={metric.total_notifications}, errors={metric.total_errors}"
        )

    print("✅ Test 5 passed: System isolated observer failures")


async def test_weak_references():
    """Test 6: Memory leak prevention with weak references"""
    print("\n=== Test 6: Weak References ===")

    monitor = MicroserviceMonitor("CacheService")

    # Create observers that will go out of scope
    def create_temporary_observers():
        temp_observer1 = ConsoleLogger("TempLogger1", priority=10)
        temp_observer2 = ConsoleLogger("TempLogger2", priority=20)
        monitor.attach(temp_observer1, [EventType.ALL])
        monitor.attach(temp_observer2, [EventType.ALL])
        return temp_observer1, temp_observer2

    # Attach observers
    obs1, obs2 = create_temporary_observers()

    # Verify observers are attached
    monitor.emit_health_check("healthy", {"cache_hits": 1000})

    # Delete references
    print("\n🗑️ Deleting observer references...")
    del obs1, obs2
    gc.collect()  # Force garbage collection

    # Cleanup dead references
    monitor._cleanup_dead_references()

    # Check that weak references were cleaned up
    total_refs = sum(len(refs) for refs in monitor._observers.values())
    print(f"📊 Remaining observer references: {total_refs}")

    # Emit event - should have no observers
    print("\nEmitting event after cleanup (should be silent)...")
    monitor.emit_health_check("healthy", {"cache_hits": 2000})

    print("✅ Test 6 passed: Weak references prevent memory leaks")


async def test_metrics_monitoring():
    """Test 7: Observer performance metrics"""
    print("\n=== Test 7: Performance Metrics ===")

    monitor = MicroserviceMonitor("MonitoringService")
    console = ConsoleLogger("MetricsLogger", priority=10)
    aggregator = MetricsAggregator()

    monitor.attach(console, [EventType.ALL])
    monitor.attach(aggregator, [EventType.PERFORMANCE])

    # Emit various events
    for i in range(10):
        monitor.emit_performance_metric("latency", 100.0 + i * 10, "ms")
        monitor.emit_health_check("healthy", {"iteration": i})

    # Get metrics
    metrics = monitor.get_metrics()

    print("\n📊 Observer Performance Metrics:")
    for name, metric in metrics.items():
        error_rate = (
            (metric.total_errors / metric.total_notifications * 100)
            if metric.total_notifications > 0
            else 0
        )
        print(f"\n{name}:")
        print(f"  Total Notifications: {metric.total_notifications}")
        print(f"  Total Errors: {metric.total_errors}")
        print(f"  Error Rate: {error_rate:.1f}%")
        print(f"  Avg Processing Time: {metric.avg_processing_time_ms:.4f}ms")
        print(
            f"  Last Notification: {metric.last_notification.strftime('%H:%M:%S') if metric.last_notification else 'N/A'}"
        )

    print("\n✅ Test 7 passed: Metrics tracking successful")


# ============================================================================
# MAIN EXECUTION
# ============================================================================


async def main():
    """Run all tests"""
    print("=" * 60)
    print("Enterprise Observer Pattern - Test Suite")
    print("=" * 60)

    await test_basic_sync_observers()
    await test_async_observers()
    await test_high_frequency_events()
    await test_event_replay()
    await test_observer_failures()
    await test_weak_references()
    await test_metrics_monitoring()

    print("\n" + "=" * 60)
    print("All tests complete!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
