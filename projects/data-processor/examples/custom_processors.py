"""Example showing how to create custom processors."""

from pipeline_framework import PipelineBuilder, PipelineData
from pipeline_framework.core.models import ProcessingContext
from pipeline_framework.core.processor import Processor


class ValidationProcessor(Processor):
    """Custom processor that validates data."""

    def __init__(self, required_fields: list[str], name: str | None = None):
        super().__init__(name)
        self._required_fields = required_fields

    def _do_process(self, context: ProcessingContext) -> ProcessingContext:
        """Validate that required fields exist."""
        missing_fields = [
            field for field in self._required_fields if field not in context.data.payload
        ]

        if missing_fields:
            raise ValueError(f"Missing required fields: {missing_fields}")

        context.data.add_metadata("validated", True)
        return context


class EnrichmentProcessor(Processor):
    """Custom processor that enriches data with additional info."""

    def _do_process(self, context: ProcessingContext) -> ProcessingContext:
        """Enrich data with computed fields."""
        # Add computed field
        if "price" in context.data.payload and "quantity" in context.data.payload:
            total = context.data.payload["price"] * context.data.payload["quantity"]
            context.data.set_payload_value("total", total)

        # Add processing timestamp
        from datetime import datetime

        context.data.add_metadata("enriched_at", datetime.now().isoformat())

        return context


def main():
    """Run custom processor example."""
    print("=== Custom Processors Example ===\n")

    # Build pipeline with custom processors
    pipeline = (
        PipelineBuilder("custom-example")
        .add_processor(ValidationProcessor(required_fields=["price", "quantity"]))
        .add_processor(EnrichmentProcessor())
        .build()
    )

    # Test with valid data
    print("Processing valid data...")
    valid_data = [
        PipelineData.create(payload={"price": 10.0, "quantity": 5, "item": "Widget"}),
        PipelineData.create(payload={"price": 15.5, "quantity": 3, "item": "Gadget"}),
    ]

    results = pipeline.execute(valid_data)

    for i, result in enumerate(results):
        print(f"\nItem {i+1}:")
        print(f"  Original: {result.data.payload}")
        print(f"  Validated: {result.data.metadata.get('validated')}")
        print(f"  Enriched at: {result.data.metadata.get('enriched_at')}")

    # Test with invalid data
    print("\n\nProcessing invalid data (missing 'quantity')...")
    invalid_data = [
        PipelineData.create(payload={"price": 10.0, "item": "Invalid Item"}),
    ]

    results = pipeline.execute(invalid_data)

    if results[0].is_failure():
        print(f"Validation failed as expected: {results[0].error}")


if __name__ == "__main__":
    main()
