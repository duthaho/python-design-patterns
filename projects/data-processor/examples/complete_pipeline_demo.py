"""Complete demonstration of all framework features."""

import logging

from pipeline_framework import PipelineBuilder
from pipeline_framework.commands.base import CommandHistory
from pipeline_framework.commands.pipeline_commands import \
    ExecutePipelineCommand
from pipeline_framework.decorators.caching import CachingDecorator
from pipeline_framework.decorators.logging import LoggingDecorator
from pipeline_framework.decorators.retry import RetryDecorator
from pipeline_framework.decorators.timing import TimingDecorator
from pipeline_framework.observability.events import EventBus
from pipeline_framework.observability.metrics import MetricsCollector
from pipeline_framework.observability.observers import (ConsoleObserver,
                                                        FileObserver)
from pipeline_framework.processors.stateful import (CounterProcessor,
                                                    DeduplicationProcessor)
from pipeline_framework.processors.transform import TransformProcessor
from pipeline_framework.strategies.transform import (FilterFieldsTransform,
                                                     UpperCaseTransform)

# Configure logging
logging.basicConfig(level=logging.INFO)


def main():
    """Run complete pipeline demonstration."""
    print("=" * 60)
    print("PIPELINE FRAMEWORK - COMPLETE DEMONSTRATION")
    print("=" * 60)
    print()

    # ========== 1. Setup Observability ==========
    print("1. Setting up observability...")
    event_bus = EventBus()
    console_observer = ConsoleObserver(verbose=False)
    file_observer = FileObserver("pipeline_execution.log", format="json")
    metrics_collector = MetricsCollector()

    event_bus.subscribe(console_observer)
    event_bus.subscribe(file_observer)
    event_bus.subscribe(metrics_collector)
    print("   ✓ Event bus configured with 3 observers")
    print()

    # ========== 2. Build Decorated Processors ==========
    print("2. Building processors with decorators...")

    # Counter with retry, logging, and timing
    counter = CounterProcessor()
    decorated_counter = TimingDecorator(
        RetryDecorator(LoggingDecorator(counter), max_retries=3, retry_delay=0.1)
    )
    print("   ✓ Counter with Timing → Retry → Logging decorators")

    # Transform with caching and timing
    transform = TransformProcessor(UpperCaseTransform())
    decorated_transform = TimingDecorator(CachingDecorator(transform, max_cache_size=100))
    print("   ✓ Transform with Timing → Caching decorators")

    # Deduplication with logging
    dedup = DeduplicationProcessor()
    decorated_dedup = LoggingDecorator(dedup)
    print("   ✓ Deduplication with Logging decorator")

    # Filter with timing
    filter_proc = TransformProcessor(FilterFieldsTransform(fields=["id", "name", "email"]))
    decorated_filter = TimingDecorator(filter_proc)
    print("   ✓ Filter with Timing decorator")
    print()

    # ========== 3. Build Pipeline ==========
    print("3. Building pipeline...")
    pipeline = (
        PipelineBuilder("complete-demo-pipeline")
        .with_source_config(
            {"type": "csv_file", "file_path": "sample_data.csv", "adapter": {"id_field": "user_id"}}
        )
        .add_processor(decorated_filter)
        .add_processor(decorated_transform)
        .add_processor(decorated_dedup)
        .add_processor(decorated_counter)
        .with_sink_config(
            {
                "type": "json_file",
                "file_path": "output.json",
                "json_lines": True,
                "adapter": {"include_processing_info": True},
            }
        )
        .with_event_bus(event_bus)
        .build()
    )
    print("   ✓ Pipeline built with 4 decorated processors")
    print("   ✓ Source: CSV file")
    print("   ✓ Sink: JSON Lines file")
    print()

    # ========== 4. Execute with Command Pattern ==========
    print("4. Executing pipeline with command pattern...")
    history = CommandHistory()

    # Read data
    from pipeline_framework.sources.factory import SourceFactory

    source = SourceFactory.create_from_config(
        {"type": "csv_file", "file_path": "sample_data.csv", "adapter": {"id_field": "user_id"}}
    )
    data = source.read()
    source.close()
    print(f"   ✓ Loaded {len(data)} items from source")

    # Execute through command
    cmd = ExecutePipelineCommand(pipeline, data)
    results = history.execute(cmd)
    print(f"   ✓ Executed pipeline, processed {len(results)} items")
    print()

    # ========== 5. Display Metrics ==========
    print("5. Pipeline Metrics:")
    metrics = metrics_collector.get_metrics("complete-demo-pipeline")
    print(f"   • Total items: {metrics.total_items}")
    print(f"   • Successful: {metrics.successful_items}")
    print(f"   • Failed: {metrics.failed_items}")
    print(f"   • Skipped: {metrics.skipped_items}")
    print(f"   • Success rate: {metrics.success_rate:.2%}")
    print(f"   • Duration: {metrics.duration}")
    print(f"   • Throughput: {metrics.items_per_second:.2f} items/sec")
    print()

    # ========== 6. Display Timing Statistics ==========
    print("6. Performance Statistics:")
    print(f"   Counter: {decorated_counter.timing_stats}")
    print(f"   Transform: {decorated_transform.timing_stats}")
    print(f"   Filter: {decorated_filter.timing_stats}")
    print()

    # ========== 7. Display Cache Statistics ==========
    print("7. Cache Statistics:")
    cache_stats = decorated_transform.wrapped.cache_stats
    print(f"   • Cache hits: {cache_stats['hits']}")
    print(f"   • Cache misses: {cache_stats['misses']}")
    print(f"   • Hit rate: {cache_stats['hit_rate']:.2%}")
    print(f"   • Cache size: {cache_stats['cache_size']}/{cache_stats['max_cache_size']}")
    print()

    # ========== 8. Demonstrate Undo ==========
    print("8. Demonstrating command undo...")
    state_before_undo = pipeline.get_state().copy()
    print(f"   State before undo: {state_before_undo}")

    history.undo()
    print(f"   State after undo: {pipeline.get_state()}")
    print("   ✓ Pipeline state restored")
    print()

    # ========== 9. Demonstrate Redo ==========
    print("9. Demonstrating command redo...")
    history.redo()
    print(f"   State after redo: {pipeline.get_state()}")
    print("   ✓ Pipeline re-executed")
    print()

    # ========== 10. Cleanup ==========
    print("10. Cleaning up...")
    file_observer.close()
    print("   ✓ File observer closed")
    print("   ✓ All resources released")
    print()

    print("=" * 60)
    print("DEMONSTRATION COMPLETE")
    print("=" * 60)
    print()
    print("Files created:")
    print("  • output.json (processed data)")
    print("  • pipeline_execution.log (event log)")
    print()
    print("Framework features demonstrated:")
    print("  ✓ 11 Design Patterns")
    print("  ✓ Event-driven observability")
    print("  ✓ Decorator stacking")
    print("  ✓ Command pattern with undo/redo")
    print("  ✓ Comprehensive metrics")
    print("  ✓ Configuration-driven pipelines")
    print("  ✓ Factory-based object creation")


if __name__ == "__main__":
    main()
