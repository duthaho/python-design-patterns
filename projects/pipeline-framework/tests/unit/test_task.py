"""Unit tests for Task."""

import pytest
from pipeline_framework.core.context import PipelineContext
from tests.conftest import AddTask, FailingTask, MultiplyTask, ReadWriteTask


class TestTask:
    """Test suite for Task implementations."""

    def test_task_has_name(self, add_task):
        """Test that tasks have a name attribute."""
        assert hasattr(add_task, "name")
        assert add_task.name == "add_10"

    def test_task_has_description(self):
        """Test that tasks can have descriptions."""
        task = AddTask("test_task", 5)
        assert hasattr(task, "description")
        assert "Add 5" in task.description

    def test_task_description_optional(self):
        """Test that description is optional."""
        # The base Task class allows optional description
        # Our test tasks always provide one, but we test the interface
        task = AddTask("simple", 1)
        assert task.name == "simple"

    def test_task_execute_modifies_context(self, add_task, empty_context):
        """Test that task execution modifies the context."""
        add_task.execute(empty_context)

        assert empty_context.has("result")
        assert empty_context.get("result") == 10

    def test_add_task_adds_correctly(self):
        """Test AddTask adds the correct value."""
        context = PipelineContext({"result": 5})
        task = AddTask("add_3", 3)

        task.execute(context)

        assert context.get("result") == 8

    def test_add_task_with_no_existing_result(self):
        """Test AddTask with no initial result (defaults to 0)."""
        context = PipelineContext()
        task = AddTask("add_7", 7)

        task.execute(context)

        assert context.get("result") == 7

    def test_multiply_task_multiplies_correctly(self):
        """Test MultiplyTask multiplies correctly."""
        context = PipelineContext({"result": 5})
        task = MultiplyTask("mult_3", 3)

        task.execute(context)

        assert context.get("result") == 15

    def test_multiply_task_with_no_existing_result(self):
        """Test MultiplyTask with no initial result (defaults to 1)."""
        context = PipelineContext()
        task = MultiplyTask("mult_5", 5, default_value=1)

        task.execute(context)

        assert context.get("result") == 5

    def test_read_write_task(self):
        """Test ReadWriteTask reads from one key and writes to another."""
        context = PipelineContext({"input": "data"})
        task = ReadWriteTask("transform", "input", "output")

        task.execute(context)

        assert context.get("output") == "processed_data"
        assert context.get("input") == "data"  # Original unchanged

    def test_failing_task_raises_exception(self, failing_task, empty_context):
        """Test that FailingTask raises an exception."""
        with pytest.raises(ValueError, match="Task failed"):
            failing_task.execute(empty_context)

    def test_failing_task_with_custom_message(self, empty_context):
        """Test FailingTask with custom error message."""
        task = FailingTask("custom_fail", "Custom error message")

        with pytest.raises(ValueError, match="Custom error message"):
            task.execute(empty_context)

    def test_task_repr(self, add_task):
        """Test task string representation."""
        repr_str = repr(add_task)

        assert "Task" in repr_str
        assert "add_10" in repr_str

    def test_multiple_tasks_on_same_context(self):
        """Test multiple tasks operating on the same context."""
        context = PipelineContext()

        task1 = AddTask("add_5", 5)
        task2 = AddTask("add_10", 10)
        task3 = MultiplyTask("mult_2", 2)

        task1.execute(context)  # result = 5
        task2.execute(context)  # result = 15
        task3.execute(context)  # result = 30

        assert context.get("result") == 30
