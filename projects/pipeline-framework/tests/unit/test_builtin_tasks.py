"""Unit tests for built-in task types."""

import logging

from pipeline_framework.core.context import PipelineContext
from pipeline_framework.factories.builtin_tasks import (FunctionTask, LogTask,
                                                        SetValueTask)


class TestFunctionTask:
    """Test suite for FunctionTask."""

    def test_function_task_initialization(self):
        """Test creating a function task."""

        def my_func(context):
            pass

        task = FunctionTask("func_task", my_func)

        assert task.name == "func_task"

    def test_function_task_executes_function(self):
        """Test that function task executes the wrapped function."""
        executed = []

        def my_func(context: PipelineContext):
            executed.append(True)
            context.set("result", "executed")

        task = FunctionTask("func_task", my_func)
        context = PipelineContext()

        task.execute(context)

        assert executed == [True]
        assert context.get("result") == "executed"

    def test_function_task_receives_context(self):
        """Test that function receives context parameter."""

        def my_func(context: PipelineContext):
            value = context.get("input", 0)
            context.set("output", value * 2)

        task = FunctionTask("func_task", my_func)
        context = PipelineContext({"input": 21})

        task.execute(context)

        assert context.get("output") == 42


class TestLogTask:
    """Test suite for LogTask."""

    def test_log_task_initialization(self):
        """Test creating a log task."""
        task = LogTask("logger", "Test message")

        assert task.name == "logger"

    def test_log_task_default_level_is_info(self):
        """Test that default log level is INFO."""
        task = LogTask("logger", "Test message")

        assert task.level == "INFO"

    def test_log_task_custom_level(self):
        """Test creating log task with custom level."""
        task = LogTask("logger", "Test message", level="WARNING")

        assert task.level == "WARNING"

    def test_log_task_executes(self, caplog):
        """Test that log task logs message."""
        task = LogTask("logger", "Test message", level="INFO")
        context = PipelineContext()

        with caplog.at_level(logging.INFO):
            task.execute(context)

        assert "Test message" in caplog.text


class TestSetValueTask:
    """Test suite for SetValueTask."""

    def test_set_value_task_initialization(self):
        """Test creating a set value task."""
        task = SetValueTask("setter", "key", "value")

        assert task.name == "setter"

    def test_set_value_task_sets_value(self):
        """Test that set value task sets value in context."""
        task = SetValueTask("setter", "result", 42)
        context = PipelineContext()

        task.execute(context)

        assert context.get("result") == 42

    def test_set_value_task_overwrites_existing(self):
        """Test that set value task overwrites existing value."""
        task = SetValueTask("setter", "key", "new_value")
        context = PipelineContext({"key": "old_value"})

        task.execute(context)

        assert context.get("key") == "new_value"

    def test_set_value_task_with_complex_value(self):
        """Test setting complex values."""
        task = SetValueTask("setter", "data", {"nested": [1, 2, 3]})
        context = PipelineContext()

        task.execute(context)

        assert context.get("data") == {"nested": [1, 2, 3]}
