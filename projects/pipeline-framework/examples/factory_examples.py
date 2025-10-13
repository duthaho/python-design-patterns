"""Examples demonstrating the factory pattern for task creation."""

import json

from pipeline_framework.core.context import PipelineContext
from pipeline_framework.core.task import Task
from pipeline_framework.events.listeners import (ConsoleListener,
                                                 StatisticsListener)
from pipeline_framework.factories import (FunctionTask, SetValueTask,
                                          TaskFactory)


# Define some custom tasks for examples
class LoadDataTask(Task):
    """Load data from a source."""

    def __init__(self, name: str, source: str = "default"):
        super().__init__(name, f"Load data from {source}")
        self.source = source

    def execute(self, context: PipelineContext) -> None:
        print(f"  [LoadDataTask] Loading from {self.source}...")
        context.set("raw_data", [1, 2, 3, 4, 5])


class FilterTask(Task):
    """Filter data based on threshold."""

    def __init__(self, name: str, min_value: int = 0):
        super().__init__(name, f"Filter data (min={min_value})")
        self.min_value = min_value

    def execute(self, context: PipelineContext) -> None:
        print(f"  [FilterTask] Filtering (min={self.min_value})...")
        data = context.get("raw_data", [])
        filtered = [x for x in data if x >= self.min_value]
        context.set("filtered_data", filtered)


class TransformTask(Task):
    """Transform data using an operation."""

    def __init__(self, name: str, operation: str = "square"):
        super().__init__(name, f"Transform using {operation}")
        self.operation = operation

    def execute(self, context: PipelineContext) -> None:
        print(f"  [TransformTask] Applying {self.operation}...")
        data = context.get("filtered_data", [])

        if self.operation == "square":
            transformed = [x**2 for x in data]
        elif self.operation == "double":
            transformed = [x * 2 for x in data]
        else:
            transformed = data

        context.set("result", transformed)


def example_1_basic_factory():
    """Example 1: Basic factory usage."""
    print("=" * 70)
    print("EXAMPLE 1: Basic Factory Usage")
    print("=" * 70)

    # Create factory and register tasks
    factory = TaskFactory()
    factory.register("load", LoadDataTask)
    factory.register("filter", FilterTask)
    factory.register("transform", TransformTask)

    # Create tasks using factory
    print("\n1. Creating tasks using factory:")
    task1 = factory.create_task("load", source="database")
    task2 = factory.create_task("filter", min_value=3)
    task3 = factory.create_task("transform", operation="square")

    print(f"  Created: {task1.name}")
    print(f"  Created: {task2.name}")
    print(f"  Created: {task3.name}")

    # Build and execute pipeline manually
    print("\n2. Executing pipeline:")
    from pipeline_framework.core.pipeline import Pipeline

    pipeline = Pipeline("manual_pipeline")
    pipeline.add_task(task1)
    pipeline.add_task(task2)
    pipeline.add_task(task3)

    result = pipeline.execute()
    print(f"\n  Final result: {result.get('result')}")
    print()


def example_2_config_based_creation():
    """Example 2: Creating pipeline from configuration."""
    print("=" * 70)
    print("EXAMPLE 2: Configuration-Based Pipeline Creation")
    print("=" * 70)

    # Setup factory
    factory = TaskFactory()
    factory.register("load", LoadDataTask)
    factory.register("filter", FilterTask)
    factory.register("transform", TransformTask)

    # Define pipeline configuration
    config = {
        "name": "data_processing_pipeline",
        "description": "Process data with filtering and transformation",
        "tasks": [
            {"type": "load", "name": "load_source_data", "params": {"source": "api"}},
            {"type": "filter", "name": "filter_small_values", "params": {"min_value": 2}},
            {"type": "transform", "name": "square_values", "params": {"operation": "square"}},
        ],
    }

    print("\nConfiguration:")
    print(json.dumps(config, indent=2))

    # Create pipeline from config
    print("\nCreating pipeline from configuration...")
    pipeline = factory.create_pipeline_from_config(config)

    print(f"\nPipeline: {pipeline.name}")
    print(f"Description: {pipeline.description}")
    print(f"Tasks: {len(pipeline)}")

    # Execute
    print("\nExecuting pipeline:")
    result = pipeline.execute()
    print(f"\nFinal result: {result.get('result')}")
    print()


def example_3_decorator_registration():
    """Example 3: Using decorator for registration."""
    print("=" * 70)
    print("EXAMPLE 3: Decorator-Based Task Registration")
    print("=" * 70)

    factory = TaskFactory()

    # Register tasks using decorator
    @factory.register_decorator("greet")
    class GreetTask(Task):
        def __init__(self, name: str, greeting: str = "Hello"):
            super().__init__(name)
            self.greeting = greeting

        def execute(self, context: PipelineContext) -> None:
            user = context.get("user", "World")
            message = f"{self.greeting}, {user}!"
            context.set("message", message)
            print(f"  {message}")

    @factory.register_decorator("log_result")
    class LogResultTask(Task):
        def __init__(self, name: str):
            super().__init__(name)

        def execute(self, context: PipelineContext) -> None:
            message = context.get("message", "No message")
            print(f"  [Log] {message}")

    print("\nTasks registered using decorators:")
    print(f"  Registered types: {factory.get_registered_types()}")

    # Create pipeline from config
    config = {
        "name": "greeting_pipeline",
        "tasks": [{"type": "greet", "params": {"greeting": "Welcome"}}, {"type": "log_result"}],
    }

    pipeline = factory.create_pipeline_from_config(config)

    print("\nExecuting pipeline:")
    result = pipeline.execute({"user": "Alice"})
    print()


def example_4_builtin_tasks():
    """Example 4: Using built-in task types."""
    print("=" * 70)
    print("EXAMPLE 4: Built-in Task Types")
    print("=" * 70)

    factory = TaskFactory()
    factory.register("set_value", SetValueTask)

    # Create pipeline with built-in tasks
    config = {
        "name": "setup_pipeline",
        "description": "Initialize configuration values",
        "tasks": [
            {"type": "set_value", "params": {"key": "environment", "value": "production"}},
            {"type": "set_value", "params": {"key": "version", "value": "1.0.0"}},
            {"type": "set_value", "params": {"key": "debug", "value": False}},
        ],
    }

    print("\nConfiguration:")
    print(json.dumps(config, indent=2))

    pipeline = factory.create_pipeline_from_config(config)
    result = pipeline.execute()

    print("\nConfiguration values set:")
    print(f"  environment: {result.get('environment')}")
    print(f"  version: {result.get('version')}")
    print(f"  debug: {result.get('debug')}")
    print()


def example_5_function_tasks():
    """Example 5: Using function tasks."""
    print("=" * 70)
    print("EXAMPLE 5: Function Tasks (No Class Needed)")
    print("=" * 70)

    from pipeline_framework.core.pipeline import Pipeline

    # Define simple functions
    def load_config(context: PipelineContext):
        print("  Loading configuration...")
        context.set("config", {"host": "localhost", "port": 8080})

    def validate_config(context: PipelineContext):
        print("  Validating configuration...")
        config = context.get("config", {})
        is_valid = "host" in config and "port" in config
        context.set("valid", is_valid)
        print(f"  Configuration valid: {is_valid}")

    def apply_config(context: PipelineContext):
        if context.get("valid", False):
            print("  Applying configuration...")
            context.set("applied", True)
        else:
            print("  Skipping - invalid configuration")
            context.set("applied", False)

    # Create pipeline with function tasks
    pipeline = Pipeline("function_pipeline")
    pipeline.add_task(FunctionTask("load", load_config))
    pipeline.add_task(FunctionTask("validate", validate_config))
    pipeline.add_task(FunctionTask("apply", apply_config))

    print("\nExecuting pipeline with function tasks:")
    result = pipeline.execute()

    print(f"\nFinal state:")
    print(f"  Config: {result.get('config')}")
    print(f"  Valid: {result.get('valid')}")
    print(f"  Applied: {result.get('applied')}")
    print()


def example_6_global_default_factory():
    """Example 6: Using the global default factory."""
    print("=" * 70)
    print("EXAMPLE 6: Global Default Factory (Singleton Pattern)")
    print("=" * 70)

    # Get default factory instance
    factory = TaskFactory.get_default()

    # Register tasks globally
    factory.register("load", LoadDataTask)
    factory.register("filter", FilterTask)

    print("\nRegistered tasks in default factory:")
    print(f"  {factory.get_registered_types()}")

    # Anywhere else in the application...
    print("\nAccessing default factory from another location:")
    another_ref = TaskFactory.get_default()

    print(f"  Same instance? {another_ref is factory}")
    print(f"  Still has registrations? {another_ref.is_registered('load')}")

    # Create pipeline using default factory
    config = {
        "name": "global_pipeline",
        "tasks": [
            {"type": "load", "params": {"source": "cache"}},
            {"type": "filter", "params": {"min_value": 1}},
        ],
    }

    pipeline = another_ref.create_pipeline_from_config(config)

    print("\nExecuting pipeline from default factory:")
    result = pipeline.execute()
    print(f"  Filtered data: {result.get('filtered_data')}")
    print()


def example_7_with_events():
    """Example 7: Factory-created pipeline with event listeners."""
    print("=" * 70)
    print("EXAMPLE 7: Factory + Events Integration")
    print("=" * 70)

    factory = TaskFactory()
    factory.register("load", LoadDataTask)
    factory.register("filter", FilterTask)
    factory.register("transform", TransformTask)

    config = {
        "name": "monitored_pipeline",
        "tasks": [
            {"type": "load"},
            {"type": "filter", "params": {"min_value": 3}},
            {"type": "transform", "params": {"operation": "double"}},
        ],
    }

    # Create pipeline and add listeners
    pipeline = factory.create_pipeline_from_config(config)

    console_listener = ConsoleListener(verbose=True)
    stats_listener = StatisticsListener()

    pipeline.add_listener(console_listener)
    pipeline.add_listener(stats_listener)

    print("\nExecuting monitored pipeline:\n")
    result = pipeline.execute()

    print("\n" + "=" * 70)
    print("STATISTICS:")
    print("=" * 70)
    stats = stats_listener.get_statistics()
    print(f"Tasks executed: {stats['tasks_started']}")
    print(f"Tasks completed: {stats['tasks_completed']}")
    print(f"Success rate: {stats['success_rate'] * 100:.0f}%")
    print(f"Final result: {result.get('result')}")
    print()


def example_8_json_config_file():
    """Example 8: Loading pipeline from JSON file."""
    print("=" * 70)
    print("EXAMPLE 8: Pipeline from JSON Configuration File")
    print("=" * 70)

    # Simulate JSON config file
    json_config = """
    {
        "name": "etl_pipeline",
        "description": "Extract, Transform, Load pipeline",
        "tasks": [
            {
                "type": "load",
                "name": "extract_data",
                "params": {"source": "database"}
            },
            {
                "type": "filter",
                "name": "filter_valid",
                "params": {"min_value": 1}
            },
            {
                "type": "transform",
                "name": "transform_data",
                "params": {"operation": "square"}
            }
        ]
    }
    """

    print("\nJSON Configuration:")
    print(json_config)

    # Parse JSON and create pipeline
    config = json.loads(json_config)

    factory = TaskFactory()
    factory.register("load", LoadDataTask)
    factory.register("filter", FilterTask)
    factory.register("transform", TransformTask)

    pipeline = factory.create_pipeline_from_config(config)

    print(f"\nCreated pipeline: {pipeline.name}")
    print(f"Description: {pipeline.description}")
    print(f"Number of tasks: {len(pipeline)}")

    print("\nExecuting pipeline:")
    result = pipeline.execute()
    print(f"\nFinal result: {result.get('result')}")
    print()


def main():
    """Run all examples."""
    print("\n" + "=" * 70)
    print("PIPELINE FRAMEWORK - FACTORY PATTERN EXAMPLES")
    print("=" * 70)
    print()

    example_1_basic_factory()
    input("Press Enter to continue to Example 2...")

    example_2_config_based_creation()
    input("Press Enter to continue to Example 3...")

    example_3_decorator_registration()
    input("Press Enter to continue to Example 4...")

    example_4_builtin_tasks()
    input("Press Enter to continue to Example 5...")

    example_5_function_tasks()
    input("Press Enter to continue to Example 6...")

    example_6_global_default_factory()
    input("Press Enter to continue to Example 7...")

    example_7_with_events()
    input("Press Enter to continue to Example 8...")

    example_8_json_config_file()

    print("=" * 70)
    print("ALL EXAMPLES COMPLETED!")
    print("=" * 70)


if __name__ == "__main__":
    main()
