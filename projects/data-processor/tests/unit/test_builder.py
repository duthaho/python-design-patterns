"""Tests for pipeline builder."""

import pytest
from pipeline_framework.core.builder import PipelineBuilder
from pipeline_framework.core.pipeline import Pipeline
from pipeline_framework.processors.stateful import CounterProcessor
from pipeline_framework.strategies.state import InMemoryStateStorage
from pipeline_framework.utils.exceptions import BuilderException


class TestPipelineBuilder:
    """Test PipelineBuilder."""

    def test_builder_creates_pipeline(self):
        """Test basic pipeline creation."""
        builder = PipelineBuilder("test-pipeline")
        processor = CounterProcessor()

        pipeline = (
            builder.add_processor(processor).with_state_storage(InMemoryStateStorage()).build()
        )

        assert isinstance(pipeline, Pipeline)
        assert pipeline.pipeline_id == "test-pipeline"

    def test_builder_requires_at_least_one_processor(self):
        """Test that builder requires at least one processor."""
        builder = PipelineBuilder("test-pipeline")

        with pytest.raises(BuilderException) as exc_info:
            builder.build()

        assert "at least one processor" in str(exc_info.value).lower()

    def test_builder_uses_default_state_storage(self):
        """Test that builder uses default state storage if none provided."""
        builder = PipelineBuilder("test-pipeline")
        processor = CounterProcessor()

        pipeline = builder.add_processor(processor).build()

        assert isinstance(pipeline, Pipeline)
        # Pipeline should work with default storage
        from pipeline_framework.core.models import PipelineData

        data = [PipelineData.create(payload={})]
        results = pipeline.execute(data)
        assert len(results) == 1

    def test_builder_chains_multiple_processors(self):
        """Test chaining multiple processors."""
        builder = PipelineBuilder("test-pipeline")
        proc1 = CounterProcessor(name="Counter1")
        proc2 = CounterProcessor(name="Counter2")
        proc3 = CounterProcessor(name="Counter3")

        pipeline = builder.add_processor(proc1).add_processor(proc2).add_processor(proc3).build()

        from pipeline_framework.core.models import PipelineData

        data = [PipelineData.create(payload={})]
        results = pipeline.execute(data)

        # All three processors should have incremented the count
        assert results[0].state["processed_count"] == 3
        assert all(
            name in results[0].processing_history for name in ["Counter1", "Counter2", "Counter3"]
        )

    def test_builder_fluent_interface(self):
        """Test fluent interface returns self."""
        builder = PipelineBuilder("test-pipeline")
        proc = CounterProcessor()
        storage = InMemoryStateStorage()

        # Each method should return the builder for chaining
        result1 = builder.add_processor(proc)
        assert result1 is builder

        result2 = builder.with_state_storage(storage)
        assert result2 is builder

    def test_builder_reset(self):
        """Test resetting builder."""
        builder = PipelineBuilder("test-pipeline")
        proc1 = CounterProcessor()

        builder.add_processor(proc1).with_state_storage(InMemoryStateStorage())
        builder.reset()

        # After reset, should not be able to build without adding processors
        with pytest.raises(BuilderException):
            builder.build()
