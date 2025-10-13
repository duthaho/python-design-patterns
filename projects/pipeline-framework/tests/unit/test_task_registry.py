"""Unit tests for TaskRegistry."""

import pytest
from pipeline_framework.core.context import PipelineContext
from pipeline_framework.core.task import Task
from pipeline_framework.factories.exceptions import TaskRegistrationException
from pipeline_framework.factories.task_registry import TaskRegistry


class SimpleTask(Task):
    """Simple test task."""

    def __init__(self, name: str):
        super().__init__(name)

    def execute(self, context: PipelineContext) -> None:
        pass


class AnotherTask(Task):
    """Another test task."""

    def __init__(self, name: str):
        super().__init__(name)

    def execute(self, context: PipelineContext) -> None:
        pass


class TestTaskRegistry:
    """Test suite for TaskRegistry."""

    def test_registry_initialization(self):
        """Test creating a registry."""
        registry = TaskRegistry()
        assert len(registry) == 0

    def test_register_task(self):
        """Test registering a task."""
        registry = TaskRegistry()
        registry.register("simple", SimpleTask)

        assert registry.has("simple")
        assert registry.get("simple") == SimpleTask

    def test_register_multiple_tasks(self):
        """Test registering multiple tasks."""
        registry = TaskRegistry()
        registry.register("simple", SimpleTask)
        registry.register("another", AnotherTask)

        assert len(registry) == 2
        assert registry.has("simple")
        assert registry.has("another")

    def test_register_duplicate_task_without_override_raises(self):
        """Test that registering duplicate without override raises exception."""
        registry = TaskRegistry()
        registry.register("simple", SimpleTask)

        with pytest.raises(TaskRegistrationException):
            registry.register("simple", AnotherTask, override=False)

    def test_register_duplicate_task_with_override(self):
        """Test that registering duplicate with override works."""
        registry = TaskRegistry()
        registry.register("simple", SimpleTask)
        registry.register("simple", AnotherTask, override=True)

        assert registry.get("simple") == AnotherTask

    def test_register_non_task_class_raises(self):
        """Test that registering non-Task class raises exception."""
        registry = TaskRegistry()

        class NotATask:
            pass

        with pytest.raises(TaskRegistrationException):
            registry.register("invalid", NotATask)

    def test_unregister_task(self):
        """Test unregistering a task."""
        registry = TaskRegistry()
        registry.register("simple", SimpleTask)

        registry.unregister("simple")

        assert not registry.has("simple")
        assert registry.get("simple") is None

    def test_unregister_nonexistent_task(self):
        """Test that unregistering nonexistent task doesn't raise error."""
        registry = TaskRegistry()

        # Should not raise
        registry.unregister("nonexistent")

    def test_get_nonexistent_task_returns_none(self):
        """Test that getting nonexistent task returns None."""
        registry = TaskRegistry()

        assert registry.get("nonexistent") is None

    def test_has_returns_false_for_nonexistent(self):
        """Test has() returns False for nonexistent task."""
        registry = TaskRegistry()

        assert not registry.has("nonexistent")

    def test_get_all_types(self):
        """Test getting all registered task types."""
        registry = TaskRegistry()
        registry.register("simple", SimpleTask)
        registry.register("another", AnotherTask)

        types = registry.get_all_types()

        assert len(types) == 2
        assert "simple" in types
        assert "another" in types

    def test_get_all_types_empty_registry(self):
        """Test get_all_types on empty registry."""
        registry = TaskRegistry()

        types = registry.get_all_types()

        assert types == []

    def test_clear_registry(self):
        """Test clearing the registry."""
        registry = TaskRegistry()
        registry.register("simple", SimpleTask)
        registry.register("another", AnotherTask)

        registry.clear()

        assert len(registry) == 0
        assert not registry.has("simple")

    def test_len_returns_correct_count(self):
        """Test __len__ returns correct count."""
        registry = TaskRegistry()

        assert len(registry) == 0

        registry.register("simple", SimpleTask)
        assert len(registry) == 1

        registry.register("another", AnotherTask)
        assert len(registry) == 2

    def test_contains_operator(self):
        """Test 'in' operator support."""
        registry = TaskRegistry()
        registry.register("simple", SimpleTask)

        assert "simple" in registry
        assert "nonexistent" not in registry
