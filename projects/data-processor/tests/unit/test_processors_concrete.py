"""Tests for concrete processor implementations."""

from pipeline_framework.core.models import PipelineData, ProcessingContext
from pipeline_framework.processors.stateful import (AggregatorProcessor,
                                                    CounterProcessor,
                                                    DeduplicationProcessor)
from pipeline_framework.processors.transform import TransformProcessor
from pipeline_framework.strategies.transform import UpperCaseTransform


class TestTransformProcessor:
    """Test TransformProcessor."""

    def test_applies_transformation(self):
        """Test that processor applies the strategy."""
        strategy = UpperCaseTransform()
        processor = TransformProcessor(strategy)

        data = PipelineData.create(payload={"name": "alice"})
        context = ProcessingContext(data=data, state={})

        result = processor.process(context)

        assert result.data.payload["name"] == "ALICE"
        assert result.is_success()


class TestCounterProcessor:
    """Test CounterProcessor."""

    def test_counts_single_item(self):
        """Test counting a single item."""
        processor = CounterProcessor()
        data = PipelineData.create(payload={})
        context = ProcessingContext(data=data, state={})

        result = processor.process(context)

        assert result.state["processed_count"] == 1

    def test_counts_multiple_items(self):
        """Test counting multiple items."""
        processor = CounterProcessor()
        state = {}

        for i in range(5):
            data = PipelineData.create(payload={"id": i})
            context = ProcessingContext(data=data, state=state)
            result = processor.process(context)
            state = result.state

        assert state["processed_count"] == 5

    def test_custom_counter_key(self):
        """Test custom counter key."""
        processor = CounterProcessor(counter_key="my_counter")
        data = PipelineData.create(payload={})
        context = ProcessingContext(data=data, state={})

        result = processor.process(context)

        assert result.state["my_counter"] == 1
        assert "processed_count" not in result.state


class TestDeduplicationProcessor:
    """Test DeduplicationProcessor."""

    def test_allows_first_occurrence(self):
        """Test that first occurrence is processed."""
        processor = DeduplicationProcessor()
        data = PipelineData.create(payload={"value": "test"})
        data.id = "unique-1"
        context = ProcessingContext(data=data, state={})

        result = processor.process(context)

        assert result.is_success()
        assert "unique-1" in result.state["seen_ids"]

    def test_skips_duplicate(self):
        """Test that duplicate is skipped."""
        processor = DeduplicationProcessor()
        state = {}

        # First occurrence
        data1 = PipelineData.create(payload={"value": "test1"})
        data1.id = "duplicate-id"
        context1 = ProcessingContext(data=data1, state=state)
        result1 = processor.process(context1)

        assert result1.is_success()

        # Duplicate occurrence
        data2 = PipelineData.create(payload={"value": "test2"})
        data2.id = "duplicate-id"
        context2 = ProcessingContext(data=data2, state=result1.state)
        result2 = processor.process(context2)

        assert result2.is_skip()

    def test_allows_different_ids(self):
        """Test that different IDs are all processed."""
        processor = DeduplicationProcessor()
        state = {}

        ids = ["id-1", "id-2", "id-3"]
        for item_id in ids:
            data = PipelineData.create(payload={})
            data.id = item_id
            context = ProcessingContext(data=data, state=state)
            result = processor.process(context)
            state = result.state

            assert result.is_success()

        assert len(state["seen_ids"]) == 3
        assert all(item_id in state["seen_ids"] for item_id in ids)


class TestAggregatorProcessor:
    """Test AggregatorProcessor."""

    def test_aggregates_single_value(self):
        """Test aggregating a single value."""
        processor = AggregatorProcessor(field="score")
        data = PipelineData.create(payload={"score": 85})
        context = ProcessingContext(data=data, state={})

        result = processor.process(context)

        assert result.state["aggregated_values"] == [85]

    def test_aggregates_multiple_values(self):
        """Test aggregating multiple values."""
        processor = AggregatorProcessor(field="price")
        state = {}
        prices = [10.5, 20.0, 15.75, 30.25]

        for price in prices:
            data = PipelineData.create(payload={"price": price})
            context = ProcessingContext(data=data, state=state)
            result = processor.process(context)
            state = result.state

        assert state["aggregated_values"] == prices

    def test_custom_aggregation_key(self):
        """Test custom aggregation key."""
        processor = AggregatorProcessor(field="amount", aggregation_key="all_amounts")
        data = PipelineData.create(payload={"amount": 100})
        context = ProcessingContext(data=data, state={})

        result = processor.process(context)

        assert result.state["all_amounts"] == [100]
        assert "aggregated_values" not in result.state

    def test_handles_missing_field(self):
        """Test handling when field is missing from payload."""
        processor = AggregatorProcessor(field="missing_field")
        data = PipelineData.create(payload={"other_field": "value"})
        context = ProcessingContext(data=data, state={})

        result = processor.process(context)

        # Should aggregate None for missing field
        assert result.state["aggregated_values"] == [None]
