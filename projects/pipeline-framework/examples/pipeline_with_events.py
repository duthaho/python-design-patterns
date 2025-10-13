"""Example demonstrating pipeline with event listeners."""

from pipeline_framework.core.context import PipelineContext
from pipeline_framework.core.pipeline import Pipeline
from pipeline_framework.core.task import Task
from pipeline_framework.events.listeners import (ConsoleListener,
                                                 StatisticsListener)


# Define some example tasks
class LoadDataTask(Task):
    """Example task that loads data."""

    def __init__(self):
        super().__init__("load_data", "Load data from source")

    def execute(self, context: PipelineContext) -> None:
        print("  [LoadDataTask] Loading data...")
        context.set("raw_data", [1, 2, 3, 4, 5, 6, 7, 8, 9, 10])


class FilterDataTask(Task):
    """Example task that filters data."""

    def __init__(self, min_value: int):
        super().__init__("filter_data", f"Filter data (min={min_value})")
        self.min_value = min_value

    def execute(self, context: PipelineContext) -> None:
        print(f"  [FilterDataTask] Filtering data (keeping values >= {self.min_value})...")
        raw_data = context.get("raw_data", [])
        filtered = [x for x in raw_data if x >= self.min_value]
        context.set("filtered_data", filtered)


class TransformDataTask(Task):
    """Example task that transforms data."""

    def __init__(self):
        super().__init__("transform_data", "Square each value")

    def execute(self, context: PipelineContext) -> None:
        print("  [TransformDataTask] Transforming data...")
        filtered_data = context.get("filtered_data", [])
        transformed = [x**2 for x in filtered_data]
        context.set("transformed_data", transformed)


class ComputeStatsTask(Task):
    """Example task that computes statistics."""

    def __init__(self):
        super().__init__("compute_stats", "Compute statistics")

    def execute(self, context: PipelineContext) -> None:
        print("  [ComputeStatsTask] Computing statistics...")
        data = context.get("transformed_data", [])
        if data:
            context.set("count", len(data))
            context.set("sum", sum(data))
            context.set("average", sum(data) / len(data))
            context.set("min", min(data))
            context.set("max", max(data))


def example_1_verbose_console():
    """Example 1: Pipeline with verbose console output."""
    print("=" * 60)
    print("EXAMPLE 1: Pipeline with Verbose Console Listener")
    print("=" * 60)

    # Create pipeline
    pipeline = Pipeline("data_processing_pipeline", "Process and analyze data")

    # Add verbose console listener
    console_listener = ConsoleListener(verbose=True)
    pipeline.add_listener(console_listener)

    # Add tasks
    pipeline.add_task(LoadDataTask())
    pipeline.add_task(FilterDataTask(min_value=5))
    pipeline.add_task(TransformDataTask())
    pipeline.add_task(ComputeStatsTask())

    # Execute
    print("\nExecuting pipeline...\n")
    result = pipeline.execute()

    # Print results
    print("\n" + "=" * 60)
    print("RESULTS:")
    print("=" * 60)
    print(f"Count: {result.get('count')}")
    print(f"Sum: {result.get('sum')}")
    print(f"Average: {result.get('average'):.2f}")
    print(f"Min: {result.get('min')}")
    print(f"Max: {result.get('max')}")
    print()


def example_2_statistics_collection():
    """Example 2: Pipeline with statistics collection."""
    print("=" * 60)
    print("EXAMPLE 2: Pipeline with Statistics Collection")
    print("=" * 60)

    # Create pipeline
    pipeline = Pipeline("stats_pipeline")

    # Add statistics listener (no console output)
    stats_listener = StatisticsListener()
    pipeline.add_listener(stats_listener)

    # Add tasks
    pipeline.add_task(LoadDataTask())
    pipeline.add_task(FilterDataTask(min_value=3))
    pipeline.add_task(TransformDataTask())
    pipeline.add_task(ComputeStatsTask())

    # Execute
    print("\nExecuting pipeline (quiet mode)...\n")
    result = pipeline.execute()

    # Get and display statistics
    stats = stats_listener.get_statistics()
    print("\n" + "=" * 60)
    print("PIPELINE STATISTICS:")
    print("=" * 60)
    print(f"Tasks Started: {stats['tasks_started']}")
    print(f"Tasks Completed: {stats['tasks_completed']}")
    print(f"Tasks Failed: {stats['tasks_failed']}")
    print(f"Success Rate: {stats['success_rate'] * 100:.1f}%")
    print(f"Task Names: {', '.join(stats['task_names'])}")
    print()


def example_3_multiple_listeners():
    """Example 3: Pipeline with multiple listeners."""
    print("=" * 60)
    print("EXAMPLE 3: Pipeline with Multiple Listeners")
    print("=" * 60)

    # Create pipeline
    pipeline = Pipeline("multi_listener_pipeline")

    # Add multiple listeners
    console_listener = ConsoleListener(verbose=True)
    stats_listener = StatisticsListener()

    pipeline.add_listener(console_listener)
    pipeline.add_listener(stats_listener)

    # Add tasks
    pipeline.add_task(LoadDataTask())
    pipeline.add_task(FilterDataTask(min_value=7))
    pipeline.add_task(TransformDataTask())

    # Execute
    print("\nExecuting pipeline with multiple listeners...\n")
    result = pipeline.execute()

    # Display both console output AND statistics
    print("\n" + "=" * 60)
    print("STATISTICS SUMMARY:")
    print("=" * 60)
    stats = stats_listener.get_statistics()
    print(f"✓ {stats['tasks_completed']}/{stats['tasks_started']} tasks completed")
    print(f"✓ Success rate: {stats['success_rate'] * 100:.0f}%")
    print()


def example_4_error_handling():
    """Example 4: Pipeline with error and event handling."""
    print("=" * 60)
    print("EXAMPLE 4: Error Handling with Events")
    print("=" * 60)

    class FailingTask(Task):
        """Task that intentionally fails."""

        def __init__(self):
            super().__init__("failing_task", "This task will fail")

        def execute(self, context: PipelineContext) -> None:
            print("  [FailingTask] About to fail...")
            raise ValueError("Intentional failure for demonstration")

    # Create pipeline
    pipeline = Pipeline("error_demo_pipeline")

    # Add listeners
    console_listener = ConsoleListener(verbose=True)
    stats_listener = StatisticsListener()

    pipeline.add_listener(console_listener)
    pipeline.add_listener(stats_listener)

    # Add tasks (one will fail)
    pipeline.add_task(LoadDataTask())
    pipeline.add_task(FailingTask())  # This will fail
    pipeline.add_task(TransformDataTask())  # This won't execute

    # Execute and handle error
    print("\nExecuting pipeline (will fail)...\n")
    try:
        result = pipeline.execute()
    except Exception as e:
        print(f"\n⚠️  Pipeline failed as expected: {e}")

    # Check statistics
    print("\n" + "=" * 60)
    print("STATISTICS AFTER FAILURE:")
    print("=" * 60)
    stats = stats_listener.get_statistics()
    print(f"Tasks Started: {stats['tasks_started']}")
    print(f"Tasks Completed: {stats['tasks_completed']}")
    print(f"Tasks Failed: {stats['tasks_failed']}")
    print(f"Failed Tasks: {', '.join(stats['failed_task_names'])}")
    print()


def example_5_listener_reuse():
    """Example 5: Reusing listeners across multiple pipelines."""
    print("=" * 60)
    print("EXAMPLE 5: Reusing Listeners Across Pipelines")
    print("=" * 60)

    # Create a single statistics listener
    stats_listener = StatisticsListener()

    # Pipeline 1
    print("\n--- Pipeline 1: Quick Process ---")
    pipeline1 = Pipeline("quick_pipeline")
    pipeline1.add_listener(stats_listener)
    pipeline1.add_task(LoadDataTask())
    pipeline1.execute()

    stats = stats_listener.get_statistics()
    print(f"After Pipeline 1: {stats['tasks_completed']} tasks completed")

    # Pipeline 2 (reusing same listener)
    print("\n--- Pipeline 2: Full Process ---")
    pipeline2 = Pipeline("full_pipeline")
    pipeline2.add_listener(stats_listener)
    pipeline2.add_task(LoadDataTask())
    pipeline2.add_task(FilterDataTask(min_value=5))
    pipeline2.add_task(TransformDataTask())
    pipeline2.execute()

    stats = stats_listener.get_statistics()
    print(f"After Pipeline 2: {stats['tasks_completed']} total tasks completed")

    # Reset and start fresh
    print("\n--- Resetting Statistics ---")
    stats_listener.reset()

    # Pipeline 3 (with fresh stats)
    print("\n--- Pipeline 3: After Reset ---")
    pipeline3 = Pipeline("fresh_pipeline")
    pipeline3.add_listener(stats_listener)
    pipeline3.add_task(LoadDataTask())
    pipeline3.execute()

    stats = stats_listener.get_statistics()
    print(f"After Reset: {stats['tasks_completed']} tasks completed (fresh count)")
    print()


def main():
    """Run all examples."""
    print("\n" + "=" * 60)
    print("PIPELINE FRAMEWORK - EVENT SYSTEM EXAMPLES")
    print("=" * 60)
    print()

    example_1_verbose_console()
    input("Press Enter to continue to Example 2...")

    example_2_statistics_collection()
    input("Press Enter to continue to Example 3...")

    example_3_multiple_listeners()
    input("Press Enter to continue to Example 4...")

    example_4_error_handling()
    input("Press Enter to continue to Example 5...")

    example_5_listener_reuse()

    print("=" * 60)
    print("ALL EXAMPLES COMPLETED!")
    print("=" * 60)


if __name__ == "__main__":
    main()
