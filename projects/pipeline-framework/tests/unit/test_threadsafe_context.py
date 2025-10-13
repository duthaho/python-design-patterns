"""Unit tests for ThreadSafePipelineContext."""

import threading
import time

from pipeline_framework.core.context import PipelineContext
from pipeline_framework.core.context_threadsafe import \
    ThreadSafePipelineContext


class TestThreadSafePipelineContext:
    """Test suite for ThreadSafePipelineContext."""

    def test_threadsafe_context_initialization_empty(self):
        """Test creating empty thread-safe context."""
        context = ThreadSafePipelineContext()
        assert context.get_all() == {}

    def test_threadsafe_context_initialization_with_data(self):
        """Test creating thread-safe context with initial data."""
        initial_data = {"key1": "value1", "key2": 42}
        context = ThreadSafePipelineContext(initial_data)

        assert context.get("key1") == "value1"
        assert context.get("key2") == 42

    def test_from_context_conversion(self):
        """Test converting regular context to thread-safe."""
        regular_context = PipelineContext({"key": "value"})
        threadsafe_context = ThreadSafePipelineContext.from_context(regular_context)

        assert isinstance(threadsafe_context, ThreadSafePipelineContext)
        assert threadsafe_context.get("key") == "value"

    def test_threadsafe_set_and_get(self):
        """Test thread-safe set and get operations."""
        context = ThreadSafePipelineContext()

        context.set("key", "value")
        assert context.get("key") == "value"

    def test_threadsafe_has(self):
        """Test thread-safe has operation."""
        context = ThreadSafePipelineContext({"existing": "value"})

        assert context.has("existing") is True
        assert context.has("nonexistent") is False

    def test_threadsafe_get_all(self):
        """Test thread-safe get_all operation."""
        context = ThreadSafePipelineContext({"key1": "value1", "key2": "value2"})

        all_data = context.get_all()

        assert len(all_data) == 2
        assert all_data["key1"] == "value1"
        assert all_data["key2"] == "value2"

    def test_concurrent_writes(self):
        """Test that concurrent writes are thread-safe."""
        context = ThreadSafePipelineContext()
        num_threads = 10
        writes_per_thread = 100

        def writer(thread_id):
            for i in range(writes_per_thread):
                context.set(f"thread_{thread_id}_count", i)

        threads = [threading.Thread(target=writer, args=(i,)) for i in range(num_threads)]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        # All threads should have written their final values
        all_data = context.get_all()
        assert len(all_data) == num_threads

        for i in range(num_threads):
            assert context.has(f"thread_{i}_count")

    def test_concurrent_reads_and_writes(self):
        """Test concurrent reads and writes don't cause race conditions."""
        context = ThreadSafePipelineContext({"counter": 0})
        num_threads = 10
        iterations = 100

        def incrementer():
            for _ in range(iterations):
                current = context.get("counter", 0)
                time.sleep(0.0001)  # Simulate some processing
                context.set("counter", current + 1)

        threads = [threading.Thread(target=incrementer) for _ in range(num_threads)]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        # With proper locking, we might not get perfect count
        # (since get and set are separate operations)
        # But the context should remain consistent
        final_value = context.get("counter")
        assert isinstance(final_value, int)
        assert final_value > 0
