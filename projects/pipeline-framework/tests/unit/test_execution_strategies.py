"""Unit tests for execution strategies."""

import threading
import time

import pytest
from pipeline_framework.core.context import PipelineContext
from pipeline_framework.core.task import Task
from pipeline_framework.strategies import (ConditionalStrategy,
                                           ParallelStrategy,
                                           SequentialStrategy)
from pipeline_framework.utils.exceptions import TaskExecutionError
from tests.conftest import AddTask, FailingTask, MultiplyTask


class RecordingTask(Task):
    """Task that records when it executes."""

    execution_order = []
    execution_lock = threading.Lock()

    def __init__(self, name: str, delay: float = 0):
        super().__init__(name)
        self.delay = delay

    def execute(self, context: PipelineContext) -> None:
        if self.delay > 0:
            time.sleep(self.delay)

        with self.execution_lock:
            RecordingTask.execution_order.append(self.name)

        context.set(f"{self.name}_executed", True)

    @classmethod
    def reset(cls):
        cls.execution_order = []


class TestSequentialStrategy:
    """Test suite for SequentialStrategy."""

    def setup_method(self):
        """Reset recording before each test."""
        RecordingTask.reset()

    def test_sequential_strategy_initialization(self):
        """Test creating sequential strategy."""
        strategy = SequentialStrategy()
        assert strategy is not None

    def test_sequential_executes_tasks_in_order(self):
        """Test that tasks execute in the order they were added."""
        strategy = SequentialStrategy()
        tasks = [
            RecordingTask("task1"),
            RecordingTask("task2"),
            RecordingTask("task3"),
        ]
        context = PipelineContext()

        strategy.execute(tasks, context)

        assert RecordingTask.execution_order == ["task1", "task2", "task3"]
        assert context.get("task1_executed") is True
        assert context.get("task2_executed") is True
        assert context.get("task3_executed") is True

    def test_sequential_stops_on_failure(self):
        """Test that sequential strategy stops on first failure."""
        strategy = SequentialStrategy()
        tasks = [
            RecordingTask("task1"),
            FailingTask("failing_task"),
            RecordingTask("task3"),  # Should not execute
        ]
        context = PipelineContext()

        with pytest.raises(TaskExecutionError):
            strategy.execute(tasks, context)

        assert context.get("task1_executed") is True
        assert context.get("task3_executed") is None  # Never executed

    def test_sequential_with_data_flow(self):
        """Test that data flows between tasks."""
        strategy = SequentialStrategy()
        tasks = [
            AddTask("add1", 10),
            AddTask("add2", 20),
            MultiplyTask("mult", 2),
        ]
        context = PipelineContext()

        strategy.execute(tasks, context)

        # (0 + 10 + 20) * 2 = 60
        assert context.get("result") == 60

    def test_get_name(self):
        """Test strategy name."""
        strategy = SequentialStrategy()
        assert "Sequential" in strategy.get_name()


class TestParallelStrategy:
    """Test suite for ParallelStrategy."""

    def setup_method(self):
        """Reset recording before each test."""
        RecordingTask.reset()

    def test_parallel_strategy_initialization(self):
        """Test creating parallel strategy."""
        strategy = ParallelStrategy(max_workers=4)
        assert strategy is not None
        assert strategy.max_workers == 4

    def test_parallel_executes_all_tasks(self):
        """Test that all tasks execute (order may vary)."""
        strategy = ParallelStrategy(max_workers=3)
        tasks = [
            RecordingTask("task1"),
            RecordingTask("task2"),
            RecordingTask("task3"),
        ]
        context = PipelineContext()

        strategy.execute(tasks, context)

        # All tasks should execute (order not guaranteed)
        assert len(RecordingTask.execution_order) == 3
        assert "task1" in RecordingTask.execution_order
        assert "task2" in RecordingTask.execution_order
        assert "task3" in RecordingTask.execution_order

    def test_parallel_faster_than_sequential(self):
        """Test that parallel execution is actually faster."""
        delay = 0.1  # 100ms per task

        # Sequential: should take ~300ms
        sequential_strategy = SequentialStrategy()
        sequential_tasks = [RecordingTask(f"seq_{i}", delay) for i in range(3)]
        context = PipelineContext()

        start = time.time()
        sequential_strategy.execute(sequential_tasks, context)
        sequential_time = time.time() - start

        RecordingTask.reset()

        # Parallel: should take ~100ms (all at once)
        parallel_strategy = ParallelStrategy(max_workers=3)
        parallel_tasks = [RecordingTask(f"par_{i}", delay) for i in range(3)]
        context = PipelineContext()

        start = time.time()
        parallel_strategy.execute(parallel_tasks, context)
        parallel_time = time.time() - start

        # Parallel should be at least 2x faster
        assert parallel_time < sequential_time / 2

    def test_parallel_with_failure_stops_execution(self):
        """Test that failure in one task stops other tasks."""
        strategy = ParallelStrategy(max_workers=3)
        tasks = [
            RecordingTask("task1", delay=0.2),
            FailingTask("failing_task"),
            RecordingTask("task3", delay=0.2),
        ]
        context = PipelineContext()

        with pytest.raises(TaskExecutionError):
            strategy.execute(tasks, context)

    def test_parallel_with_different_worker_counts(self):
        """Test parallel strategy with different worker counts."""
        for max_workers in [1, 2, 4]:
            RecordingTask.reset()
            strategy = ParallelStrategy(max_workers=max_workers)
            tasks = [RecordingTask(f"task_{i}") for i in range(5)]
            context = PipelineContext()

            strategy.execute(tasks, context)

            assert len(RecordingTask.execution_order) == 5

    def test_parallel_uses_threadsafe_context(self):
        """Test that parallel strategy uses thread-safe context."""
        from pipeline_framework.core.context_threadsafe import \
            ThreadSafePipelineContext

        strategy = ParallelStrategy(max_workers=3)

        # Create counter tasks that increment
        class CounterTask(Task):
            def __init__(self, name):
                super().__init__(name)

            def execute(self, context):
                for _ in range(10):
                    current = context.get("counter", 0)
                    context.set("counter", current + 1)

        tasks = [CounterTask(f"counter_{i}") for i in range(5)]
        context = ThreadSafePipelineContext({"counter": 0})

        strategy.execute(tasks, context)

        # With thread-safe context, counter should have a valid value
        counter_value = context.get("counter")
        assert isinstance(counter_value, int)
        assert counter_value > 0


class TestConditionalStrategy:
    """Test suite for ConditionalStrategy."""

    def setup_method(self):
        """Reset recording before each test."""
        RecordingTask.reset()

    def test_conditional_strategy_initialization(self):
        """Test creating conditional strategy."""
        condition = lambda task, context: True
        strategy = ConditionalStrategy(condition)
        assert strategy is not None

    def test_conditional_executes_when_true(self):
        """Test that tasks execute when condition is True."""
        condition = lambda task, context: True
        strategy = ConditionalStrategy(condition)
        tasks = [RecordingTask("task1"), RecordingTask("task2")]
        context = PipelineContext()

        strategy.execute(tasks, context)

        assert len(RecordingTask.execution_order) == 2

    def test_conditional_skips_when_false(self):
        """Test that tasks are skipped when condition is False."""
        condition = lambda task, context: False
        strategy = ConditionalStrategy(condition)
        tasks = [RecordingTask("task1"), RecordingTask("task2")]
        context = PipelineContext()

        strategy.execute(tasks, context)

        assert len(RecordingTask.execution_order) == 0
        assert context.get("task1_executed") is None

    def test_conditional_based_on_task_name(self):
        """Test conditional execution based on task name."""
        # Only execute tasks with "important" in name
        condition = lambda task, context: "important" in task.name
        strategy = ConditionalStrategy(condition)

        tasks = [
            RecordingTask("important_task1"),
            RecordingTask("optional_task"),
            RecordingTask("important_task2"),
        ]
        context = PipelineContext()

        strategy.execute(tasks, context)

        assert len(RecordingTask.execution_order) == 2
        assert "important_task1" in RecordingTask.execution_order
        assert "important_task2" in RecordingTask.execution_order
        assert "optional_task" not in RecordingTask.execution_order

    def test_conditional_based_on_context(self):
        """Test conditional execution based on context state."""
        # Only execute if context has "enabled" flag
        condition = lambda task, context: context.get("execute_tasks", False)
        strategy = ConditionalStrategy(condition)

        tasks = [RecordingTask("task1"), RecordingTask("task2")]

        # First: context without flag
        context1 = PipelineContext()
        strategy.execute(tasks, context1)
        assert len(RecordingTask.execution_order) == 0

        RecordingTask.reset()

        # Second: context with flag
        context2 = PipelineContext({"execute_tasks": True})
        strategy.execute(tasks, context2)
        assert len(RecordingTask.execution_order) == 2

    def test_conditional_mixed_execution(self):
        """Test that some tasks execute and some are skipped."""
        # Execute only even-numbered tasks
        condition = lambda task, context: int(task.name.split("_")[1]) % 2 == 0
        strategy = ConditionalStrategy(condition)

        tasks = [RecordingTask(f"task_{i}") for i in range(5)]
        context = PipelineContext()

        strategy.execute(tasks, context)

        # task_0, task_2, task_4 should execute
        assert len(RecordingTask.execution_order) == 3
        assert "task_0" in RecordingTask.execution_order
        assert "task_2" in RecordingTask.execution_order
        assert "task_4" in RecordingTask.execution_order
