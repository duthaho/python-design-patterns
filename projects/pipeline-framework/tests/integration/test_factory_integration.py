"""Integration tests for factory system."""

from pipeline_framework.core.context import PipelineContext
from pipeline_framework.core.task import Task
from pipeline_framework.events.listeners import StatisticsListener
from pipeline_framework.factories import (FunctionTask, SetValueTask,
                                          TaskFactory)


class AddTask(Task):
    """Test task that adds a value."""

    def __init__(self, name: str, value: int):
        super().__init__(name)
        self.value = value

    def execute(self, context: PipelineContext) -> None:
        current = context.get("result", 0)
        context.set("result", current + self.value)


class MultiplyTask(Task):
    """Test task that multiplies a value."""

    def __init__(self, name: str, multiplier: int):
        super().__init__(name)
        self.multiplier = multiplier

    def execute(self, context: PipelineContext) -> None:
        current = context.get("result", 1)
        context.set("result", current * self.multiplier)


class TestFactoryIntegration:
    """Integration tests for factory system."""

    def teardown_method(self):
        """Reset factory after each test."""
        TaskFactory.reset_default()

    def test_end_to_end_pipeline_creation(self):
        """Test complete pipeline creation from config."""
        factory = TaskFactory()
        factory.register("add", AddTask)
        factory.register("multiply", MultiplyTask)

        config = {
            "name": "math_pipeline",
            "description": "Mathematical operations",
            "tasks": [
                {"type": "add", "params": {"value": 10}},
                {"type": "multiply", "params": {"multiplier": 2}},
                {"type": "add", "params": {"value": 5}},
            ],
        }

        pipeline = factory.create_pipeline_from_config(config)
        result = pipeline.execute()

        # (0 + 10) * 2 + 5 = 25
        assert result.get("result") == 25

    def test_pipeline_with_builtin_tasks(self):
        """Test pipeline using built-in task types."""
        factory = TaskFactory()
        factory.register("set_value", SetValueTask)

        config = {
            "name": "setup_pipeline",
            "tasks": [
                {"type": "set_value", "params": {"key": "input", "value": 100}},
                {"type": "set_value", "params": {"key": "multiplier", "value": 2}},
            ],
        }

        pipeline = factory.create_pipeline_from_config(config)
        result = pipeline.execute()

        assert result.get("input") == 100
        assert result.get("multiplier") == 2

    def test_pipeline_with_function_task(self):
        """Test pipeline with function tasks."""
        factory = TaskFactory()

        def double_result(context: PipelineContext):
            value = context.get("value", 0)
            context.set("result", value * 2)

        func_task = FunctionTask("doubler", double_result)

        pipeline = factory.create_pipeline_from_config({"name": "func_pipeline", "tasks": []})
        pipeline.add_task(func_task)

        result = pipeline.execute({"value": 21})

        assert result.get("result") == 42

    def test_factory_with_events(self):
        """Test factory-created pipeline with event listeners."""
        factory = TaskFactory()
        factory.register("add", AddTask)

        config = {
            "name": "event_pipeline",
            "tasks": [
                {"type": "add", "params": {"value": 5}},
                {"type": "add", "params": {"value": 10}},
            ],
        }

        pipeline = factory.create_pipeline_from_config(config)
        stats_listener = StatisticsListener()
        pipeline.add_listener(stats_listener)

        result = pipeline.execute()

        assert result.get("result") == 15
        stats = stats_listener.get_statistics()
        assert stats["tasks_completed"] == 2

    def test_decorator_registration_in_practice(self):
        """Test using decorator for task registration."""
        factory = TaskFactory()

        @factory.register_decorator("custom")
        class CustomTask(Task):
            def __init__(self, name: str, message: str = ""):
                super().__init__(name)
                self.message = message

            def execute(self, context: PipelineContext) -> None:
                context.set("message", self.message)

        config = {
            "name": "custom_pipeline",
            "tasks": [{"type": "custom", "params": {"message": "Hello from factory!"}}],
        }

        pipeline = factory.create_pipeline_from_config(config)
        result = pipeline.execute()

        assert result.get("message") == "Hello from factory!"

    def test_multiple_pipelines_same_factory(self):
        """Test creating multiple pipelines from same factory."""
        factory = TaskFactory()
        factory.register("add", AddTask)

        config1 = {"name": "pipeline1", "tasks": [{"type": "add", "params": {"value": 10}}]}
        config2 = {"name": "pipeline2", "tasks": [{"type": "add", "params": {"value": 20}}]}

        pipeline1 = factory.create_pipeline_from_config(config1)
        pipeline2 = factory.create_pipeline_from_config(config2)

        result1 = pipeline1.execute()
        result2 = pipeline2.execute()

        assert result1.get("result") == 10
        assert result2.get("result") == 20

    def test_default_factory_persistence(self):
        """Test that default factory maintains registrations."""
        factory1 = TaskFactory.get_default()
        factory1.register("add", AddTask)

        # Get default again - should have same registrations
        factory2 = TaskFactory.get_default()

        assert factory2.is_registered("add")

        task = factory2.create_task("add", value=5)
        assert isinstance(task, AddTask)
