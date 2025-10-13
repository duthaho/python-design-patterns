"""Pytest configuration and shared fixtures."""

import pytest
from pipeline_framework.core.context import PipelineContext
from pipeline_framework.core.task import Task
from pipeline_framework.factories import TaskFactory


@pytest.fixture
def empty_context():
    """Provide an empty pipeline context."""
    return PipelineContext()


@pytest.fixture
def context_with_data():
    """Provide a context with some initial data."""
    return PipelineContext({"input": 10, "name": "test", "value": 42})


# Concrete task implementations for testing
class AddTask(Task):
    """Test task that adds a number to the context."""

    def __init__(self, name: str, value_to_add: int):
        super().__init__(name, f"Add {value_to_add} to result")
        self.value_to_add = value_to_add

    def execute(self, context: PipelineContext) -> None:
        current = context.get("result", 0)
        context.set("result", current + self.value_to_add)


class MultiplyTask(Task):
    """Test task that multiplies a value in the context."""

    def __init__(self, name: str, multiplier: int, default_value: int = 0):
        super().__init__(name, f"Multiply result by {multiplier}")
        self.multiplier = multiplier
        self.default_value = default_value

    def execute(self, context: PipelineContext) -> None:
        current = context.get("result", self.default_value)
        context.set("result", current * self.multiplier)


class ReadWriteTask(Task):
    """Test task that reads one key and writes to another."""

    def __init__(self, name: str, read_key: str, write_key: str):
        super().__init__(name, f"Read {read_key}, write to {write_key}")
        self.read_key = read_key
        self.write_key = write_key

    def execute(self, context: PipelineContext) -> None:
        value = context.get(self.read_key, "default")
        context.set(self.write_key, f"processed_{value}")


class FailingTask(Task):
    """Test task that always fails."""

    def __init__(self, name: str = "failing_task", error_message: str = "Task failed"):
        super().__init__(name, "A task that fails")
        self.error_message = error_message

    def execute(self, context: PipelineContext) -> None:
        raise ValueError(self.error_message)


class CounterTask(Task):
    """Test task that increments a counter (for testing execution order)."""

    def __init__(self, name: str, counter_key: str = "counter"):
        super().__init__(name, "Increment counter")
        self.counter_key = counter_key

    def execute(self, context: PipelineContext) -> None:
        current = context.get(self.counter_key, 0)
        context.set(self.counter_key, current + 1)


@pytest.fixture
def add_task():
    """Provide an AddTask instance."""
    return AddTask("add_10", 10)


@pytest.fixture
def multiply_task():
    """Provide a MultiplyTask instance."""
    return MultiplyTask("multiply_by_2", 2)


@pytest.fixture
def failing_task():
    """Provide a FailingTask instance."""
    return FailingTask()


@pytest.fixture
def factory():
    """Provide a fresh TaskFactory instance."""
    factory = TaskFactory()
    yield factory
    # Cleanup is automatic since it's a new instance


@pytest.fixture
def factory_with_tasks():
    """Provide a factory with common tasks registered."""
    from tests.conftest import AddTask, MultiplyTask

    factory = TaskFactory()
    factory.register("add", AddTask)
    factory.register("multiply", MultiplyTask)
    yield factory


# Add teardown for tests using default factory
@pytest.fixture(autouse=True)
def reset_default_factory():
    """Reset default factory after each test."""
    yield
    TaskFactory.reset_default()
