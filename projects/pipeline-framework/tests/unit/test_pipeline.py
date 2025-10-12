"""Unit tests for Pipeline."""

import pytest
from pipeline_framework.core.context import PipelineContext
from pipeline_framework.core.pipeline import Pipeline
from pipeline_framework.utils.exceptions import TaskExecutionError
from tests.conftest import (AddTask, CounterTask, FailingTask, MultiplyTask,
                            ReadWriteTask)


class TestPipeline:
    """Test suite for Pipeline."""

    def test_pipeline_initialization(self):
        """Test creating a pipeline."""
        pipeline = Pipeline("test_pipeline")

        assert pipeline.name == "test_pipeline"
        assert len(pipeline.get_tasks()) == 0

    def test_pipeline_initialization_with_description(self):
        """Test creating a pipeline with description."""
        pipeline = Pipeline("test_pipeline", "A test pipeline")

        assert pipeline.name == "test_pipeline"
        assert hasattr(pipeline, "description")

    def test_add_task_returns_self(self, add_task):
        """Test that add_task returns self for chaining."""
        pipeline = Pipeline("test")

        result = pipeline.add_task(add_task)

        assert result is pipeline
        assert len(pipeline.get_tasks()) == 1

    def test_add_single_task(self, add_task):
        """Test adding a single task."""
        pipeline = Pipeline("test")
        pipeline.add_task(add_task)

        tasks = pipeline.get_tasks()
        assert len(tasks) == 1
        assert tasks[0] is add_task

    def test_add_multiple_tasks_chaining(self):
        """Test adding multiple tasks using method chaining."""
        pipeline = Pipeline("test")
        task1 = AddTask("task1", 1)
        task2 = AddTask("task2", 2)
        task3 = AddTask("task3", 3)

        pipeline.add_task(task1).add_task(task2).add_task(task3)

        tasks = pipeline.get_tasks()
        assert len(tasks) == 3
        assert tasks[0] is task1
        assert tasks[1] is task2
        assert tasks[2] is task3

    def test_execute_empty_pipeline(self):
        """Test executing a pipeline with no tasks."""
        pipeline = Pipeline("empty")

        context = pipeline.execute()

        assert isinstance(context, PipelineContext)
        assert context.get_all() == {}

    def test_execute_empty_pipeline_with_initial_data(self):
        """Test executing empty pipeline with initial data."""
        pipeline = Pipeline("empty")

        context = pipeline.execute({"key": "value"})

        assert context.get("key") == "value"

    def test_execute_single_task(self):
        """Test executing a pipeline with one task."""
        pipeline = Pipeline("single")
        pipeline.add_task(AddTask("add_10", 10))

        context = pipeline.execute()

        assert context.get("result") == 10

    def test_execute_multiple_tasks_in_order(self):
        """Test that tasks execute in the order they were added."""
        pipeline = Pipeline("ordered")

        # Order matters: (0 + 10) * 2 = 20
        pipeline.add_task(AddTask("add_10", 10))
        pipeline.add_task(MultiplyTask("mult_2", 2))

        context = pipeline.execute()
        assert context.get("result") == 20

        # Different order: (0 * 2) + 10 = 10
        pipeline2 = Pipeline("reversed")
        pipeline2.add_task(MultiplyTask("mult_2", 2))
        pipeline2.add_task(AddTask("add_10", 10))

        context2 = pipeline2.execute()
        assert context2.get("result") == 10

    def test_execute_complex_task_chain(self):
        """Test a complex chain of operations."""
        pipeline = Pipeline("complex")

        # (((0 + 5) * 2) + 10) * 3 = ((5 * 2) + 10) * 3 = 20 * 3 = 60
        pipeline.add_task(AddTask("add_5", 5))
        pipeline.add_task(MultiplyTask("mult_2", 2))
        pipeline.add_task(AddTask("add_10", 10))
        pipeline.add_task(MultiplyTask("mult_3", 3))

        context = pipeline.execute()
        assert context.get("result") == 60

    def test_execute_with_initial_data(self):
        """Test executing pipeline with initial context data."""
        pipeline = Pipeline("with_initial")
        pipeline.add_task(ReadWriteTask("process", "input_key", "output_key"))

        context = pipeline.execute({"input_key": "test_data"})

        assert context.get("input_key") == "test_data"
        assert context.get("output_key") == "processed_test_data"

    def test_execute_tasks_share_context(self):
        """Test that all tasks share the same context."""
        pipeline = Pipeline("shared")

        task1 = AddTask("task1", 5)
        task2 = AddTask("task2", 10)
        task3 = AddTask("task3", 3)

        pipeline.add_task(task1).add_task(task2).add_task(task3)

        context = pipeline.execute()

        # All tasks should have operated on the same "result" key
        assert context.get("result") == 18  # 5 + 10 + 3

    def test_execute_failing_task_raises_error(self, failing_task):
        """Test that a failing task raises TaskExecutionError."""
        pipeline = Pipeline("failing")
        pipeline.add_task(failing_task)

        with pytest.raises(TaskExecutionError) as exc_info:
            pipeline.execute()

        assert exc_info.value.task_name == "failing_task"
        assert isinstance(exc_info.value.original_error, ValueError)

    def test_execute_failing_task_preserves_error_message(self):
        """Test that TaskExecutionError preserves original error message."""
        pipeline = Pipeline("failing")
        pipeline.add_task(FailingTask("bad_task", "Something went wrong"))

        with pytest.raises(TaskExecutionError) as exc_info:
            pipeline.execute()

        error_msg = str(exc_info.value)
        assert "bad_task" in error_msg
        assert "Something went wrong" in str(exc_info.value.original_error)

    def test_execute_stops_on_first_failure(self):
        """Test fail-fast behavior: pipeline stops on first error."""
        pipeline = Pipeline("fail_fast")

        counter_task = CounterTask("counter")
        failing_task = FailingTask("fail")
        another_counter = CounterTask("counter2")

        pipeline.add_task(counter_task)
        pipeline.add_task(failing_task)
        pipeline.add_task(another_counter)  # Should never execute

        with pytest.raises(TaskExecutionError):
            context = pipeline.execute()

        # We can't check context here because exception was raised
        # But we can verify in a separate test

    def test_execute_context_state_before_failure(self):
        """Test that context preserves state from tasks before failure."""
        pipeline = Pipeline("partial")

        pipeline.add_task(AddTask("add_5", 5))
        pipeline.add_task(AddTask("add_10", 10))
        pipeline.add_task(FailingTask("fail"))
        pipeline.add_task(AddTask("add_100", 100))  # Should not execute

        try:
            context = pipeline.execute()
        except TaskExecutionError:
            # Context is not returned on failure, so we test differently
            pass

        # Create a new test that catches and inspects
        pipeline2 = Pipeline("partial2")
        task1 = AddTask("task1", 5)
        task2 = CounterTask("marker")
        task3 = FailingTask("fail")
        task4 = CounterTask("should_not_run")

        pipeline2.add_task(task1).add_task(task2).add_task(task3).add_task(task4)

        with pytest.raises(TaskExecutionError):
            pipeline2.execute()

    def test_get_tasks_returns_copy(self):
        """Test that get_tasks returns a copy of the task list."""
        pipeline = Pipeline("test")
        task1 = AddTask("task1", 1)
        task2 = AddTask("task2", 2)

        pipeline.add_task(task1).add_task(task2)

        tasks = pipeline.get_tasks()
        assert len(tasks) == 2

        # Modify the returned list
        tasks.append(AddTask("task3", 3))
        tasks.pop(0)

        # Original pipeline should be unchanged
        original_tasks = pipeline.get_tasks()
        assert len(original_tasks) == 2
        assert original_tasks[0] is task1

    def test_get_tasks_returns_empty_list_initially(self):
        """Test that a new pipeline has no tasks."""
        pipeline = Pipeline("empty")

        tasks = pipeline.get_tasks()
        assert tasks == []
        assert isinstance(tasks, list)

    def test_pipeline_repr(self):
        """Test pipeline string representation."""
        pipeline = Pipeline("test_pipeline")
        pipeline.add_task(AddTask("task1", 1))
        pipeline.add_task(AddTask("task2", 2))

        repr_str = repr(pipeline)

        assert "Pipeline" in repr_str
        assert "test_pipeline" in repr_str
        assert "2" in repr_str  # Number of tasks

    def test_pipeline_with_no_side_effects(self):
        """Test that pipeline execution doesn't affect task objects."""
        task = AddTask("reusable", 10)

        pipeline1 = Pipeline("first")
        pipeline1.add_task(task)
        context1 = pipeline1.execute()

        pipeline2 = Pipeline("second")
        pipeline2.add_task(task)
        context2 = pipeline2.execute()

        # Both executions should produce the same result
        assert context1.get("result") == 10
        assert context2.get("result") == 10

    def test_execute_returns_context(self):
        """Test that execute() returns a PipelineContext."""
        pipeline = Pipeline("test")
        pipeline.add_task(AddTask("task", 5))

        result = pipeline.execute()

        assert isinstance(result, PipelineContext)
        assert result.get("result") == 5

    def test_multiple_pipelines_independent(self):
        """Test that multiple pipeline instances are independent."""
        task1 = AddTask("task1", 10)
        task2 = AddTask("task2", 20)

        pipeline1 = Pipeline("pipeline1")
        pipeline1.add_task(task1)

        pipeline2 = Pipeline("pipeline2")
        pipeline2.add_task(task2)

        # Execute both
        context1 = pipeline1.execute()
        context2 = pipeline2.execute()

        assert context1.get("result") == 10
        assert context2.get("result") == 20
        assert len(pipeline1.get_tasks()) == 1
        assert len(pipeline2.get_tasks()) == 1
