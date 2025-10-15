"""Tests for pipeline orchestrator."""

from pipeline_framework.core.models import PipelineData
from pipeline_framework.core.pipeline import Pipeline
from pipeline_framework.processors.stateful import CounterProcessor
from pipeline_framework.strategies.state import InMemoryStateStorage


class TestPipeline:
    """Test Pipeline orchestrator."""

    def test_execute_single_item(self):
        """Test executing pipeline with single item."""
        processor = CounterProcessor()
        storage = InMemoryStateStorage()
        pipeline = Pipeline("test-pipeline", processor, storage)

        data = [PipelineData.create(payload={"value": 1})]
        results = pipeline.execute(data)

        assert len(results) == 1
        assert results[0].is_success()
        assert results[0].state["processed_count"] == 1

    def test_execute_multiple_items(self):
        """Test executing pipeline with multiple items."""
        processor = CounterProcessor()
        storage = InMemoryStateStorage()
        pipeline = Pipeline("test-pipeline", processor, storage)

        data = [PipelineData.create(payload={"value": i}) for i in range(5)]
        results = pipeline.execute(data)

        assert len(results) == 5
        # Counter should increment for each item
        assert results[-1].state["processed_count"] == 5

    def test_state_persists_across_runs(self):
        """Test that state persists across multiple pipeline runs."""
        processor = CounterProcessor()
        storage = InMemoryStateStorage()
        pipeline = Pipeline("test-pipeline", processor, storage)

        # First run
        data1 = [PipelineData.create(payload={}) for _ in range(3)]
        results1 = pipeline.execute(data1)
        assert results1[-1].state["processed_count"] == 3

        # Second run - state should persist
        data2 = [PipelineData.create(payload={}) for _ in range(2)]
        results2 = pipeline.execute(data2)
        assert results2[-1].state["processed_count"] == 5

    def test_execute_single_convenience_method(self):
        """Test execute_single convenience method."""
        processor = CounterProcessor()
        storage = InMemoryStateStorage()
        pipeline = Pipeline("test-pipeline", processor, storage)

        data = PipelineData.create(payload={"value": 42})
        result = pipeline.execute_single(data)

        assert result.is_success()
        assert result.state["processed_count"] == 1

    def test_get_state(self):
        """Test getting current state."""
        processor = CounterProcessor()
        storage = InMemoryStateStorage()
        pipeline = Pipeline("test-pipeline", processor, storage)

        # Initially empty
        state = pipeline.get_state()
        assert state == {}

        # After execution
        data = [PipelineData.create(payload={})]
        pipeline.execute(data)

        state = pipeline.get_state()
        assert state["processed_count"] == 1

    def test_clear_state(self):
        """Test clearing pipeline state."""
        processor = CounterProcessor()
        storage = InMemoryStateStorage()
        pipeline = Pipeline("test-pipeline", processor, storage)

        # Execute to create state
        data = [PipelineData.create(payload={}) for _ in range(3)]
        pipeline.execute(data)
        assert pipeline.get_state()["processed_count"] == 3

        # Clear state
        pipeline.clear_state()
        assert pipeline.get_state() == {}

        # Next execution should start from 0
        pipeline.execute(data)
        assert pipeline.get_state()["processed_count"] == 3

    def test_different_pipelines_have_isolated_state(self):
        """Test that different pipelines have isolated state."""
        processor1 = CounterProcessor()
        processor2 = CounterProcessor()
        storage = InMemoryStateStorage()

        pipeline1 = Pipeline("pipeline-1", processor1, storage)
        pipeline2 = Pipeline("pipeline-2", processor2, storage)

        # Execute on pipeline 1
        data = [PipelineData.create(payload={})]
        pipeline1.execute(data)

        # Pipeline 1 should have count, pipeline 2 should not
        assert pipeline1.get_state()["processed_count"] == 1
        assert pipeline2.get_state() == {}
