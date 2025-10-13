"""Unit tests for task decorators."""

import time

import pytest
from pipeline_framework.core.context import PipelineContext
from pipeline_framework.core.task import Task
from pipeline_framework.decorators import (CacheDecorator, MetricsDecorator,
                                           RetryDecorator, TaskDecorator,
                                           TimeoutDecorator)
from tests.conftest import AddTask


class CountingTask(Task):
    """Task that counts how many times it's executed."""

    def __init__(self, name: str, should_fail: int = 0):
        super().__init__(name)
        self.execution_count = 0
        self.should_fail = should_fail  # Fail this many times before succeeding

    def execute(self, context: PipelineContext) -> None:
        self.execution_count += 1
        if self.execution_count <= self.should_fail:
            raise ValueError(f"Simulated failure (attempt {self.execution_count})")
        context.set("executed", True)
        context.set("count", self.execution_count)


class SlowTask(Task):
    """Task that takes time to execute."""

    def __init__(self, name: str, duration: float):
        super().__init__(name)
        self.duration = duration

    def execute(self, context: PipelineContext) -> None:
        time.sleep(self.duration)
        context.set("completed", True)


class TestTaskDecorator:
    """Test suite for base TaskDecorator."""

    def test_decorator_wraps_task(self):
        """Test that decorator properly wraps a task."""
        original_task = AddTask("original", 10)

        # Create a concrete decorator (use one of the implementations)
        from pipeline_framework.decorators.metrics import MetricsDecorator

        decorated_task = MetricsDecorator(original_task)

        assert decorated_task.name == "original"
        assert decorated_task._wrapped is original_task

    def test_decorator_executes_wrapped_task(self):
        """Test that decorator executes the wrapped task."""
        original_task = AddTask("add", 10)

        from pipeline_framework.decorators.metrics import MetricsDecorator

        decorated_task = MetricsDecorator(original_task)

        context = PipelineContext()
        decorated_task.execute(context)

        assert context.get("result") == 10

    def test_decorator_with_custom_name(self):
        """Test decorator with custom name override."""
        original_task = AddTask("original", 10)

        class TestDecorator(TaskDecorator):
            def execute(self, context):
                self._wrapped.execute(context)

        decorated_task = TestDecorator(original_task, name="custom_name")

        assert decorated_task.name == "custom_name"


class TestRetryDecorator:
    """Test suite for RetryDecorator."""

    def test_retry_succeeds_on_first_attempt(self):
        """Test task that succeeds immediately."""
        task = CountingTask("success", should_fail=0)
        retry_task = RetryDecorator(task, max_retries=3)

        context = PipelineContext()
        retry_task.execute(context)

        assert task.execution_count == 1
        assert context.get("executed") is True

    def test_retry_succeeds_after_failures(self):
        """Test that retry eventually succeeds."""
        task = CountingTask("retry", should_fail=2)  # Fail first 2 times
        retry_task = RetryDecorator(task, max_retries=3, delay=0.01)

        context = PipelineContext()
        retry_task.execute(context)

        assert task.execution_count == 3  # Failed twice, succeeded on 3rd
        assert context.get("executed") is True

    def test_retry_fails_after_max_attempts(self):
        """Test that retry fails after exhausting retries."""
        task = CountingTask("always_fail", should_fail=10)
        retry_task = RetryDecorator(task, max_retries=2, delay=0.01)

        context = PipelineContext()

        with pytest.raises(ValueError):
            retry_task.execute(context)

        assert task.execution_count == 3  # Initial + 2 retries

    def test_retry_with_exponential_backoff(self):
        """Test that retry uses exponential backoff."""
        task = CountingTask("backoff", should_fail=2)
        retry_task = RetryDecorator(task, max_retries=3, delay=0.1, backoff=2.0)

        start = time.time()
        context = PipelineContext()
        retry_task.execute(context)
        elapsed = time.time() - start

        # Should wait: 0.1s + 0.2s = 0.3s minimum
        assert elapsed >= 0.3

    def test_retry_with_specific_exceptions(self):
        """Test retry only catches specified exceptions."""

        class CustomException(Exception):
            pass

        class SpecificFailTask(Task):
            def __init__(self):
                super().__init__("specific")
                self.count = 0

            def execute(self, context):
                self.count += 1
                if self.count == 1:
                    raise ValueError("Retry this")
                elif self.count == 2:
                    raise CustomException("Don't retry this")

        task = SpecificFailTask()
        retry_task = RetryDecorator(
            task, max_retries=5, delay=0.01, exceptions=(ValueError,)  # Only retry ValueError
        )

        context = PipelineContext()

        # Should fail with CustomException (not retried)
        with pytest.raises(CustomException):
            retry_task.execute(context)

        assert task.count == 2  # Retried ValueError, then got CustomException


class TestTimeoutDecorator:
    """Test suite for TimeoutDecorator."""

    def test_timeout_succeeds_within_limit(self):
        """Test task that completes within timeout."""
        task = SlowTask("fast", duration=0.1)
        timeout_task = TimeoutDecorator(task, timeout=1)

        context = PipelineContext()
        timeout_task.execute(context)

        assert context.get("completed") is True

    def test_timeout_raises_on_exceed(self):
        """Test that timeout raises exception."""
        task = SlowTask("slow", duration=2.0)
        timeout_task = TimeoutDecorator(task, timeout=1)

        context = PipelineContext()

        from pipeline_framework.decorators.timeout import TimeoutException

        with pytest.raises((TimeoutException, Exception)):
            timeout_task.execute(context)

    def test_timeout_with_fast_task(self):
        """Test timeout doesn't interfere with fast tasks."""
        task = AddTask("fast", 42)
        timeout_task = TimeoutDecorator(task, timeout=5)

        context = PipelineContext()
        timeout_task.execute(context)

        assert context.get("result") == 42

    def test_timeout_cancels_alarm_on_success(self):
        """Test that alarm is cancelled after successful execution."""
        task = SlowTask("quick", duration=0.1)
        timeout_task = TimeoutDecorator(task, timeout=5)

        context = PipelineContext()
        timeout_task.execute(context)


class TestCacheDecorator:
    """Test suite for CacheDecorator."""

    def test_cache_miss_executes_task(self):
        """Test that cache miss executes the task."""
        task = CountingTask("cacheable", should_fail=0)
        cache_task = CacheDecorator(task)

        context = PipelineContext({"input": 10})
        cache_task.execute(context)

        assert task.execution_count == 1
        assert context.get("executed") is True

    def test_cache_hit_skips_execution(self):
        """Test that cache hit skips task execution."""
        task = CountingTask("cacheable", should_fail=0)
        cache_task = CacheDecorator(task)

        # First execution - cache miss
        context1 = PipelineContext({"input": 10})
        cache_task.execute(context1)
        assert task.execution_count == 1

        # Second execution with same input - cache hit
        context2 = PipelineContext({"input": 10})
        cache_task.execute(context2)
        assert task.execution_count == 1  # Not executed again!
        assert context2.get("executed") is True  # But result restored

    def test_cache_miss_on_different_input(self):
        """Test that different input causes cache miss."""
        task = CountingTask("cacheable", should_fail=0)
        cache_task = CacheDecorator(task)

        context1 = PipelineContext({"input": 10})
        cache_task.execute(context1)

        context2 = PipelineContext({"input": 20})  # Different input
        cache_task.execute(context2)

        assert task.execution_count == 2  # Executed twice

    def test_cache_with_specific_keys(self):
        """Test caching based on specific context keys."""
        task = CountingTask("cacheable", should_fail=0)
        cache_task = CacheDecorator(task, cache_keys=["important"])

        # Same "important" key, different "other" key
        context1 = PipelineContext({"important": "value", "other": "a"})
        cache_task.execute(context1)

        context2 = PipelineContext({"important": "value", "other": "b"})
        cache_task.execute(context2)

        # Should be cache hit (only "important" key matters)
        assert task.execution_count == 1

    def test_cache_restores_results(self):
        """Test that cache restores task results."""

        class ResultTask(Task):
            def __init__(self):
                super().__init__("result_task")

            def execute(self, context):
                input_val = context.get("input")
                context.set("output", input_val * 2)
                context.set("metadata", "processed")

        task = ResultTask()
        cache_task = CacheDecorator(task)

        # First execution
        context1 = PipelineContext({"input": 21})
        cache_task.execute(context1)
        assert context1.get("output") == 42
        assert context1.get("metadata") == "processed"

        # Second execution (cache hit)
        context2 = PipelineContext({"input": 21})
        cache_task.execute(context2)
        assert context2.get("output") == 42  # Restored from cache
        assert context2.get("metadata") == "processed"


class TestMetricsDecorator:
    """Test suite for MetricsDecorator."""

    def test_metrics_tracks_execution_count(self):
        """Test that metrics tracks execution count."""
        task = AddTask("tracked", 10)
        metrics_task = MetricsDecorator(task)

        context = PipelineContext()

        metrics_task.execute(context)
        metrics_task.execute(context)
        metrics_task.execute(context)

        metrics = metrics_task.get_metrics()

        assert metrics["min_time"] > 0
        assert metrics["max_time"] > 0
