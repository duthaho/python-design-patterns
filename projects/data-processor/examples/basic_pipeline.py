"""Basic pipeline example."""

from pipeline_framework import PipelineBuilder, PipelineData
from pipeline_framework.processors.stateful import CounterProcessor
from pipeline_framework.processors.transform import TransformProcessor
from pipeline_framework.strategies.transform import UpperCaseTransform


def main():
    """Run a basic pipeline example."""
    print("=== Basic Pipeline Example ===\n")

    # Build a simple pipeline
    pipeline = (
        PipelineBuilder("basic-example")
        .add_processor(CounterProcessor())
        .add_processor(TransformProcessor(UpperCaseTransform()))
        .build()
    )

    # Create sample data
    data = [
        PipelineData.create(payload={"name": "alice", "city": "new york"}),
        PipelineData.create(payload={"name": "bob", "city": "san francisco"}),
        PipelineData.create(payload={"name": "charlie", "city": "boston"}),
    ]

    # Execute pipeline
    print("Processing data...")
    results = pipeline.execute(data)

    # Display results
    print(f"\nProcessed {len(results)} items")
    print(f"Total count: {results[-1].state['processed_count']}\n")

    for i, result in enumerate(results):
        print(f"Item {i+1}:")
        print(f"  Name: {result.data.payload['name']}")
        print(f"  City: {result.data.payload['city']}")
        print(f"  Status: {result.result.value}")
        print()


if __name__ == "__main__":
    main()
