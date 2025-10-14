"""Integration tests for complete pipeline scenarios."""

import pytest
from pipeline_framework import (InMemoryStateStorage, PipelineBuilder,
                                PipelineData)
from pipeline_framework.processors.stateful import (AggregatorProcessor,
                                                    CounterProcessor,
                                                    DeduplicationProcessor)
from pipeline_framework.processors.transform import TransformProcessor
from pipeline_framework.strategies.transform import (FilterFieldsTransform,
                                                     UpperCaseTransform)


class TestPipelineIntegration:
    """Integration tests for complete pipeline scenarios."""

    def test_simple_transform_pipeline(self):
        """Test a simple transformation pipeline."""
        pipeline = (
            PipelineBuilder("transform-pipeline")
            .add_processor(TransformProcessor(UpperCaseTransform()))
            .add_processor(CounterProcessor())
            .build()
        )

        data = [
            PipelineData.create(payload={"name": "alice", "city": "nyc"}),
            PipelineData.create(payload={"name": "bob", "city": "sf"}),
        ]

        results = pipeline.execute(data)

        assert len(results) == 2
        assert results[0].data.payload["name"] == "ALICE"
        assert results[1].data.payload["name"] == "BOB"
        assert results[-1].state["processed_count"] == 2

    def test_deduplication_pipeline(self):
        """Test pipeline with deduplication."""
        pipeline = (
            PipelineBuilder("dedup-pipeline")
            .add_processor(DeduplicationProcessor())
            .add_processor(CounterProcessor())
            .build()
        )

        data = [
            PipelineData(id="1", payload={"value": "first"}, metadata={}, timestamp=None),
            PipelineData(id="2", payload={"value": "second"}, metadata={}, timestamp=None),
            PipelineData(id="1", payload={"value": "duplicate"}, metadata={}, timestamp=None),
            PipelineData(id="3", payload={"value": "third"}, metadata={}, timestamp=None),
        ]

        results = pipeline.execute(data)

        # Only 3 unique IDs should be counted (1, 2, 3)
        assert results[-1].state["processed_count"] == 3
        assert results[2].is_skip()  # Duplicate should be skipped

    def test_aggregation_pipeline(self):
        """Test pipeline with aggregation."""
        pipeline = (
            PipelineBuilder("aggregation-pipeline")
            .add_processor(AggregatorProcessor(field="price"))
            .add_processor(CounterProcessor())
            .build()
        )

        data = [
            PipelineData.create(payload={"price": 10.5, "item": "A"}),
            PipelineData.create(payload={"price": 20.0, "item": "B"}),
            PipelineData.create(payload={"price": 15.75, "item": "C"}),
        ]

        results = pipeline.execute(data)

        assert results[-1].state["aggregated_values"] == [10.5, 20.0, 15.75]
        assert results[-1].state["processed_count"] == 3

    def test_complex_pipeline_with_filtering(self):
        """Test complex pipeline with multiple transformations."""
        pipeline = (
            PipelineBuilder("complex-pipeline")
            .add_processor(TransformProcessor(FilterFieldsTransform(fields=["name", "age"])))
            .add_processor(TransformProcessor(UpperCaseTransform()))
            .add_processor(CounterProcessor())
            .add_processor(AggregatorProcessor(field="age"))
            .build()
        )

        data = [
            PipelineData.create(
                payload={"name": "alice", "age": 30, "city": "NYC", "country": "USA"}
            ),
            PipelineData.create(payload={"name": "bob", "age": 25, "city": "SF", "country": "USA"}),
        ]

        results = pipeline.execute(data)

        # Check filtering worked
        assert "city" not in results[0].data.payload
        assert "country" not in results[0].data.payload

        # Check uppercase worked
        assert results[0].data.payload["name"] == "ALICE"
        assert results[1].data.payload["name"] == "BOB"

        # Check counter worked
        assert results[-1].state["processed_count"] == 2

        # Check aggregation worked
        assert results[-1].state["aggregated_values"] == [30, 25]

    def test_state_persistence_across_runs(self):
        """Test that state persists across multiple pipeline runs."""
        storage = InMemoryStateStorage()

        pipeline = (
            PipelineBuilder("persistent-pipeline")
            .add_processor(DeduplicationProcessor())
            .add_processor(CounterProcessor())
            .with_state_storage(storage)
            .build()
        )

        # First run
        data1 = [
            PipelineData(id="1", payload={"v": "a"}, metadata={}, timestamp=None),
            PipelineData(id="2", payload={"v": "b"}, metadata={}, timestamp=None),
        ]
        results1 = pipeline.execute(data1)
        assert results1[-1].state["processed_count"] == 2

        # Second run - IDs 2 and 3 (2 is duplicate)
        data2 = [
            PipelineData(id="2", payload={"v": "c"}, metadata={}, timestamp=None),
            PipelineData(id="3", payload={"v": "d"}, metadata={}, timestamp=None),
        ]
        results2 = pipeline.execute(data2)

        # Count should be 3 (not 4, because ID 2 is duplicate)
        assert results2[-1].state["processed_count"] == 3
        assert results2[0].is_skip()  # First item (ID 2) should be skipped
        assert results2[1].is_success()  # Second item (ID 3) should succeed

    def test_pipeline_with_empty_batch(self):
        """Test pipeline handling empty data batch."""
        pipeline = PipelineBuilder("empty-pipeline").add_processor(CounterProcessor()).build()

        results = pipeline.execute([])

        assert len(results) == 0
        assert pipeline.get_state() == {}

    def test_multiple_pipelines_same_storage(self):
        """Test multiple pipelines sharing same storage backend."""
        storage = InMemoryStateStorage()

        pipeline1 = (
            PipelineBuilder("pipeline-1")
            .add_processor(CounterProcessor())
            .with_state_storage(storage)
            .build()
        )

        pipeline2 = (
            PipelineBuilder("pipeline-2")
            .add_processor(CounterProcessor())
            .with_state_storage(storage)
            .build()
        )

        # Execute on both pipelines
        data = [PipelineData.create(payload={})]
        pipeline1.execute(data)
        pipeline1.execute(data)
        pipeline2.execute(data)

        # Each should have independent state
        assert pipeline1.get_state()["processed_count"] == 2
        assert pipeline2.get_state()["processed_count"] == 1
