"""Stateful pipeline example demonstrating state persistence."""

from pipeline_framework import PipelineBuilder, PipelineData
from pipeline_framework.processors.stateful import (AggregatorProcessor,
                                                    CounterProcessor,
                                                    DeduplicationProcessor)
from pipeline_framework.strategies.state import InMemoryStateStorage


def main():
    """Run a stateful pipeline example."""
    print("=== Stateful Pipeline Example ===\n")

    # Create shared state storage
    storage = InMemoryStateStorage()

    # Build pipeline with stateful processors
    pipeline = (
        PipelineBuilder("stateful-example")
        .add_processor(DeduplicationProcessor())
        .add_processor(CounterProcessor())
        .add_processor(AggregatorProcessor(field="amount"))
        .with_state_storage(storage)
        .build()
    )

    # First batch
    print("Processing first batch...")
    batch1 = [
        PipelineData(id="txn-1", payload={"amount": 100}, metadata={}, timestamp=None),
        PipelineData(id="txn-2", payload={"amount": 200}, metadata={}, timestamp=None),
        PipelineData(id="txn-3", payload={"amount": 150}, metadata={}, timestamp=None),
    ]

    results1 = pipeline.execute(batch1)
    print(f"Processed: {results1[-1].state['processed_count']} items")
    print(f"Aggregated amounts: {results1[-1].state['aggregated_values']}\n")

    # Second batch (includes duplicates)
    print("Processing second batch (with duplicates)...")
    batch2 = [
        PipelineData(
            id="txn-2", payload={"amount": 999}, metadata={}, timestamp=None
        ),  # Duplicate!
        PipelineData(id="txn-4", payload={"amount": 300}, metadata={}, timestamp=None),
        PipelineData(id="txn-5", payload={"amount": 250}, metadata={}, timestamp=None),
    ]

    results2 = pipeline.execute(batch2)
    print(f"Processed: {results2[-1].state['processed_count']} items (txn-2 was skipped)")
    print(f"Aggregated amounts: {results2[-1].state['aggregated_values']}\n")

    # Show final state
    print("Final pipeline state:")
    final_state = pipeline.get_state()
    print(f"  Total processed: {final_state['processed_count']}")
    print(f"  Unique IDs seen: {len(final_state['seen_ids'])}")
    print(f"  All amounts: {final_state['aggregated_values']}")


if __name__ == "__main__":
    main()
