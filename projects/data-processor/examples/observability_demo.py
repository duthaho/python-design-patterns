"""Demo of observability features."""

from pipeline_framework import PipelineBuilder
from pipeline_framework.decorators.logging import LoggingDecorator
from pipeline_framework.decorators.retry import RetryDecorator
from pipeline_framework.decorators.timing import TimingDecorator
from pipeline_framework.observability.events import EventBus
from pipeline_framework.observability.metrics import MetricsCollector
from pipeline_framework.observability.observers import ConsoleObserver
from pipeline_framework.processors.stateful import CounterProcessor
from pipeline_framework.processors.transform import TransformProcessor
from pipeline_framework.strategies.transform import UpperCaseTransform


def main():
    """Run observability demo."""
    print("=== Pipeline Framework Observability Demo ===\n")

    # Setup observability
    event_bus = EventBus()
    console_observer = ConsoleObserver(verbose=True)
    metrics_collector = MetricsCollector()

    event_bus.subscribe(console_observer)
    event_bus.subscribe(metrics_collector)

    # Build pipeline with decorated processors
    counter = CounterProcessor()
    transform = TransformProcessor(UpperCaseTransform())

    # Add decorators
    decorated_counter = TimingDecorator(RetryDecorator(LoggingDecorator(counter), max_retries=3))

    decorated_transform = TimingDecorator(transform)

    # Build pipeline
    pipeline = (
        PipelineBuilder("demo-pipeline")
        .with_source_config({"type": "csv_file", "file_path": "data.csv"})
        .add_processor(decorated_counter)
        .add_processor(decorated_transform)
        .with_sink_config({"type": "json_file", "file_path": "output.json"})
        .with_event_bus(event_bus)
        .build_and_run()
    )

    # Show metrics
    metrics = metrics_collector.get_metrics("demo-pipeline")
    print("\n=== Pipeline Metrics ===")
    print(f"Total items: {metrics.total_items}")
    print(f"Success rate: {metrics.success_rate:.2%}")
    print(f"Throughput: {metrics.items_per_second:.2f} items/sec")
    print(f"Duration: {metrics.duration}")

    # Show timing stats
    print("\n=== Timing Statistics ===")
    print(f"Counter: {decorated_counter.timing_stats}")
    print(f"Transform: {decorated_transform.timing_stats}")


if __name__ == "__main__":
    main()
