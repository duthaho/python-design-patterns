"""Unit tests for TaskFactory."""

import pytest
from pipeline_framework.core.context import PipelineContext
from pipeline_framework.core.task import Task
from pipeline_framework.factories.exceptions import (
    InvalidTaskConfigException, TaskNotRegisteredException)
from pipeline_framework.factories.task_factory import TaskFactory


class ConfigurableTask(Task):
    """Task with configurable parameters for testing."""

    def __init__(self, name: str, value: int = 0, description: str = ""):
        super().__init__(name, description)
        self.value = value

    def execute(self, context: PipelineContext) -> None:
        context.set("result", self.value)


class TestTaskFactory:
    """Test suite for TaskFactory."""

    def teardown_method(self):
        """Reset default factory after each test."""
        TaskFactory.reset_default()

    def test_factory_initialization(self):
        """Test creating a factory."""
        factory = TaskFactory()
        assert factory is not None

    def test_get_default_returns_singleton(self):
        """Test that get_default returns same instance."""
        factory1 = TaskFactory.get_default()
        factory2 = TaskFactory.get_default()

        assert factory1 is factory2

    def test_reset_default_creates_new_instance(self):
        """Test that reset_default allows new instance."""
        factory1 = TaskFactory.get_default()
        TaskFactory.reset_default()
        factory2 = TaskFactory.get_default()

        assert factory1 is not factory2

    def test_register_task(self):
        """Test registering a task type."""
        factory = TaskFactory()
        factory.register("configurable", ConfigurableTask)

        assert factory.is_registered("configurable")

    def test_register_decorator(self):
        """Test decorator-based registration."""
        factory = TaskFactory()

        @factory.register_decorator("decorated")
        class DecoratedTask(Task):
            def __init__(self, name: str):
                super().__init__(name)

            def execute(self, context: PipelineContext) -> None:
                pass

        assert factory.is_registered("decorated")
        assert DecoratedTask is not None  # Class still accessible

    def test_create_task_simple(self):
        """Test creating a task with minimal parameters."""
        factory = TaskFactory()
        factory.register("configurable", ConfigurableTask)

        task = factory.create_task("configurable")

        assert isinstance(task, ConfigurableTask)
        assert task.name == "configurable"

    def test_create_task_with_name(self):
        """Test creating a task with custom name."""
        factory = TaskFactory()
        factory.register("configurable", ConfigurableTask)

        task = factory.create_task("configurable", task_name="my_task")

        assert task.name == "my_task"

    def test_create_task_with_parameters(self):
        """Test creating a task with parameters."""
        factory = TaskFactory()
        factory.register("configurable", ConfigurableTask)

        task = factory.create_task("configurable", value=42, description="Test")

        assert task.value == 42
        assert task.description == "Test"

    def test_create_task_unregistered_raises(self):
        """Test creating unregistered task raises exception."""
        factory = TaskFactory()

        with pytest.raises(TaskNotRegisteredException) as exc_info:
            factory.create_task("nonexistent")

        assert "nonexistent" in str(exc_info.value)

    def test_create_task_invalid_params_raises(self):
        """Test creating task with invalid params raises exception."""
        factory = TaskFactory()
        factory.register("configurable", ConfigurableTask)

        with pytest.raises(InvalidTaskConfigException):
            factory.create_task("configurable", invalid_param=123)

    def test_create_task_from_config_minimal(self):
        """Test creating task from minimal config."""
        factory = TaskFactory()
        factory.register("configurable", ConfigurableTask)

        config = {"type": "configurable"}
        task = factory.create_task_from_config(config)

        assert isinstance(task, ConfigurableTask)

    def test_create_task_from_config_with_name(self):
        """Test creating task from config with name."""
        factory = TaskFactory()
        factory.register("configurable", ConfigurableTask)

        config = {"type": "configurable", "name": "my_custom_task"}
        task = factory.create_task_from_config(config)

        assert task.name == "my_custom_task"

    def test_create_task_from_config_with_params(self):
        """Test creating task from config with parameters."""
        factory = TaskFactory()
        factory.register("configurable", ConfigurableTask)

        config = {"type": "configurable", "params": {"value": 99, "description": "Configured task"}}
        task = factory.create_task_from_config(config)

        assert task.value == 99
        assert task.description == "Configured task"

    def test_create_task_from_config_missing_type_raises(self):
        """Test that config without type raises exception."""
        factory = TaskFactory()

        config = {"name": "task1"}

        with pytest.raises(InvalidTaskConfigException):
            factory.create_task_from_config(config)

    def test_create_pipeline_from_config(self):
        """Test creating pipeline from configuration."""
        factory = TaskFactory()
        factory.register("configurable", ConfigurableTask)

        config = {
            "name": "test_pipeline",
            "description": "Test pipeline",
            "tasks": [
                {"type": "configurable", "params": {"value": 10}},
                {"type": "configurable", "params": {"value": 20}},
            ],
        }

        pipeline = factory.create_pipeline_from_config(config)

        assert pipeline.name == "test_pipeline"
        assert pipeline.description == "Test pipeline"
        assert len(pipeline) == 2

    def test_create_pipeline_from_config_with_override_name(self):
        """Test creating pipeline with name override."""
        factory = TaskFactory()
        factory.register("configurable", ConfigurableTask)

        config = {"name": "original_name", "tasks": []}

        pipeline = factory.create_pipeline_from_config(config, pipeline_name="overridden")

        assert pipeline.name == "overridden"

    def test_create_pipeline_from_config_empty_tasks(self):
        """Test creating pipeline with no tasks."""
        factory = TaskFactory()

        config = {"name": "empty_pipeline", "tasks": []}

        pipeline = factory.create_pipeline_from_config(config)

        assert len(pipeline) == 0

    def test_get_registered_types(self):
        """Test getting all registered types."""
        factory = TaskFactory()
        factory.register("type1", ConfigurableTask)
        factory.register("type2", ConfigurableTask)

        types = factory.get_registered_types()

        assert len(types) == 2
        assert "type1" in types
        assert "type2" in types

    def test_is_registered(self):
        """Test checking if type is registered."""
        factory = TaskFactory()
        factory.register("configurable", ConfigurableTask)

        assert factory.is_registered("configurable")
        assert not factory.is_registered("nonexistent")
