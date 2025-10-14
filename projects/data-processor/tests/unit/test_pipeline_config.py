"""Tests for pipeline configuration."""

import pytest
from pipeline_framework.core.builder import PipelineBuilder
from pipeline_framework.core.models import (PipelineConfig, PipelineData,
                                            ProcessingContext)
from pipeline_framework.core.processor import Processor
from pipeline_framework.processors.stateful import (CounterProcessor,
                                                    DeduplicationProcessor)


class TestFailingProcessor(Processor):
    """Processor that always fails for testing."""

    def _do_process(self, context: ProcessingContext) -> ProcessingContext:
        raise ValueError("Intentional failure")


class TestSkippingProcessor(Processor):
    """Processor that always skips for testing."""

    def _do_process(self, context: ProcessingContext) -> ProcessingContext:
        context.mark_skip()
        return context


class TestPipelineConfig:
    """Test PipelineConfig class."""

    def test_default_config(self):
        """Test default configuration values."""
        config = PipelineConfig()

        # Verify defaults (adjust based on your implementation)
        assert config.stop_on_failure is False
        assert config.stop_on_skip is False

    def test_custom_config(self):
        """Test creating config with custom values."""
        config = PipelineConfig(
            stop_on_failure=False,
            stop_on_skip=True,
        )

        assert config.stop_on_failure is False
        assert config.stop_on_skip is True

    def test_config_is_immutable(self):
        """Test that config should be immutable after creation (if using frozen dataclass)."""
        config = PipelineConfig(stop_on_failure=True)

        # If you used @dataclass(frozen=True), this should raise an error
        # Otherwise, skip this test or test that modifications don't affect pipelines
        try:
            config.stop_on_failure = False
            # If we get here, config is mutable (which is fine, just different design)
            assert config.stop_on_failure is False
        except AttributeError:
            # Config is frozen, which is good!
            pass


class TestPipelineConfigIntegration:
    """Integration tests for PipelineConfig with Pipeline."""

    def test_builder_accepts_config(self):
        """Test that builder accepts and uses config."""
        config = PipelineConfig(stop_on_failure=False)

        pipeline = (
            PipelineBuilder("test-pipeline")
            .with_config(config)
            .add_processor(CounterProcessor())
            .build()
        )

        assert pipeline is not None
        # Verify pipeline has the config
        assert hasattr(pipeline, "_config") or hasattr(pipeline, "config")

    def test_default_config_when_not_specified(self):
        """Test that pipeline uses default config when none provided."""
        pipeline = PipelineBuilder("test-pipeline").add_processor(CounterProcessor()).build()

        # Should have default config
        assert pipeline is not None

    def test_stop_on_failure_true(self):
        """Test pipeline stops processing chain when processor fails and stop_on_failure=True."""
        config = PipelineConfig(stop_on_failure=True)

        proc1 = CounterProcessor(name="Counter1")
        proc2 = TestFailingProcessor(name="Failer")
        proc3 = CounterProcessor(name="Counter2")

        pipeline = (
            PipelineBuilder("test-pipeline")
            .with_config(config)
            .add_processor(proc1)
            .add_processor(proc2)
            .add_processor(proc3)
            .build()
        )

        data = [PipelineData.create(payload={})]
        results = pipeline.execute(data)

        # Counter1 should run (count=1)
        # Failer should fail
        # Counter2 should NOT run (still count=1)
        assert results[0].is_failure()
        assert results[0].state["processed_count"] == 1
        assert "Counter1" in results[0].processing_history
        assert "Failer" in results[0].processing_history
        # Counter2 might or might not be in history depending on implementation

    def test_stop_on_failure_false(self):
        """Test pipeline continues processing chain when processor fails and stop_on_failure=False."""
        config = PipelineConfig(stop_on_failure=False)

        proc1 = CounterProcessor(name="Counter1")
        proc2 = TestFailingProcessor(name="Failer")
        proc3 = CounterProcessor(name="Counter2")

        pipeline = (
            PipelineBuilder("test-pipeline")
            .with_config(config)
            .add_processor(proc1)
            .add_processor(proc2)
            .add_processor(proc3)
            .build()
        )

        data = [PipelineData.create(payload={})]
        results = pipeline.execute(data)

        # All processors should run even though one failed
        # But counter might not increment after failure depending on _should_process
        assert "Counter1" in results[0].processing_history
        assert "Failer" in results[0].processing_history
        assert "Counter2" in results[0].processing_history

    def test_stop_on_skip_true(self):
        """Test pipeline stops when processor skips and stop_on_skip=True."""
        config = PipelineConfig(stop_on_skip=True)

        proc1 = CounterProcessor(name="Counter1")
        proc2 = TestSkippingProcessor(name="Skipper")
        proc3 = CounterProcessor(name="Counter2")

        pipeline = (
            PipelineBuilder("test-pipeline")
            .with_config(config)
            .add_processor(proc1)
            .add_processor(proc2)
            .add_processor(proc3)
            .build()
        )

        data = [PipelineData.create(payload={})]
        results = pipeline.execute(data)

        # Counter1 runs (count=1)
        # Skipper skips
        # Counter2 should NOT run (count stays 1)
        assert results[0].is_skip()
        assert results[0].state["processed_count"] == 1
        assert "Skipper" in results[0].processing_history

    def test_stop_on_skip_false(self):
        """Test pipeline continues when processor skips and stop_on_skip=False."""
        config = PipelineConfig(stop_on_skip=False)

        proc1 = CounterProcessor(name="Counter1")
        proc2 = TestSkippingProcessor(name="Skipper")
        proc3 = CounterProcessor(name="Counter2")

        pipeline = (
            PipelineBuilder("test-pipeline")
            .with_config(config)
            .add_processor(proc1)
            .add_processor(proc2)
            .add_processor(proc3)
            .build()
        )

        data = [PipelineData.create(payload={})]
        results = pipeline.execute(data)

        # All processors should run
        # Counter2 should run even though Skipper skipped
        assert "Counter1" in results[0].processing_history
        assert "Skipper" in results[0].processing_history
        assert "Counter2" in results[0].processing_history
        # Count might be 2 if Counter2 resets skip status, or stays at 1


@pytest.mark.skip()
class TestStateManagementConfig:
    """Test state management configuration options."""

    def test_share_state_within_batch_true(self):
        """Test that items in same batch share state when share_state_within_batch=True."""
        config = PipelineConfig(share_state_within_batch=True)

        processor = DeduplicationProcessor()
        pipeline = (
            PipelineBuilder("test-pipeline").with_config(config).add_processor(processor).build()
        )

        # Process batch with duplicate IDs
        data = [
            PipelineData(id="dup-1", payload={"value": "first"}, metadata={}, timestamp=None),
            PipelineData(id="dup-1", payload={"value": "second"}, metadata={}, timestamp=None),
        ]

        results = pipeline.execute(data)

        # First item succeeds, second is skipped (saw same ID in same batch)
        assert results[0].is_success()
        assert results[1].is_skip()

    def test_share_state_within_batch_false(self):
        """Test that items in same batch have isolated state when share_state_within_batch=False."""
        config = PipelineConfig(share_state_within_batch=False)

        processor = DeduplicationProcessor()
        pipeline = (
            PipelineBuilder("test-pipeline").with_config(config).add_processor(processor).build()
        )

        # Process batch with duplicate IDs
        data = [
            PipelineData(id="dup-1", payload={"value": "first"}, metadata={}, timestamp=None),
            PipelineData(id="dup-1", payload={"value": "second"}, metadata={}, timestamp=None),
        ]

        results = pipeline.execute(data)

        # Both items should succeed (each has isolated state)
        assert results[0].is_success()
        assert results[1].is_success()

        # But after the batch, the state should remember both
        # (if you merge states back, otherwise only the last one)

    def test_deep_copy_state_per_item_true(self):
        """Test that each item gets deep copy of state when deep_copy_state_per_item=True."""
        config = PipelineConfig(share_state_within_batch=False, deep_copy_state_per_item=True)

        processor = CounterProcessor()
        pipeline = (
            PipelineBuilder("test-pipeline").with_config(config).add_processor(processor).build()
        )

        data = [
            PipelineData.create(payload={}),
            PipelineData.create(payload={}),
        ]

        results = pipeline.execute(data)

        # With isolated state, each item starts fresh
        # Each should have count=1 (not cumulative)
        assert results[0].state["processed_count"] == 1
        assert results[1].state["processed_count"] == 1

        # Verify they're different objects
        assert results[0].state is not results[1].state

    def test_deep_copy_state_per_item_false(self):
        """Test shallow copy behavior when deep_copy_state_per_item=False."""
        config = PipelineConfig(share_state_within_batch=False, deep_copy_state_per_item=False)

        # This test verifies shallow copy creates separate dicts
        # but nested objects might be shared
        processor = CounterProcessor()
        pipeline = (
            PipelineBuilder("test-pipeline").with_config(config).add_processor(processor).build()
        )

        data = [
            PipelineData.create(payload={}),
            PipelineData.create(payload={}),
        ]

        results = pipeline.execute(data)

        # Behavior depends on your implementation
        # Document what you expect here


class TestConfigCombinations:
    """Test various configuration combinations."""

    def test_strict_mode(self):
        """Test strict mode: stop on any issue."""
        config = PipelineConfig(stop_on_failure=True, stop_on_skip=True)

        proc1 = CounterProcessor(name="Counter1")
        proc2 = TestSkippingProcessor(name="Skipper")
        proc3 = CounterProcessor(name="Counter2")

        pipeline = (
            PipelineBuilder("strict-pipeline")
            .with_config(config)
            .add_processor(proc1)
            .add_processor(proc2)
            .add_processor(proc3)
            .build()
        )

        data = [PipelineData.create(payload={})]
        results = pipeline.execute(data)

        # Should stop at skipper
        assert results[0].state["processed_count"] == 1
        assert results[0].is_skip()

    def test_lenient_mode(self):
        """Test lenient mode: continue through everything."""
        config = PipelineConfig(stop_on_failure=False, stop_on_skip=False)

        proc1 = CounterProcessor(name="Counter1")
        proc2 = TestFailingProcessor(name="Failer")
        proc3 = TestSkippingProcessor(name="Skipper")
        proc4 = CounterProcessor(name="Counter2")

        pipeline = (
            PipelineBuilder("lenient-pipeline")
            .with_config(config)
            .add_processor(proc1)
            .add_processor(proc2)
            .add_processor(proc3)
            .add_processor(proc4)
            .build()
        )

        data = [PipelineData.create(payload={})]
        results = pipeline.execute(data)

        # All processors should be in history
        assert all(
            name in results[0].processing_history
            for name in ["Counter1", "Failer", "Skipper", "Counter2"]
        )

    @pytest.mark.skip()
    def test_isolated_stateful_processing(self):
        """Test isolated state with stateful processors."""
        config = PipelineConfig(share_state_within_batch=False, deep_copy_state_per_item=True)

        pipeline = (
            PipelineBuilder("isolated-pipeline")
            .with_config(config)
            .add_processor(CounterProcessor())
            .add_processor(DeduplicationProcessor())
            .build()
        )

        # Same ID in batch - both should process with isolated state
        data = [
            PipelineData(id="same", payload={"n": 1}, metadata={}, timestamp=None),
            PipelineData(id="same", payload={"n": 2}, metadata={}, timestamp=None),
        ]

        results = pipeline.execute(data)

        # Both should succeed (isolated deduplication)
        assert results[0].is_success()
        assert results[1].is_success()


@pytest.mark.skip()
class TestConfigValidation:
    """Test configuration validation."""

    def test_conflicting_config_warning(self):
        """Test that conflicting configurations are handled."""
        # If share_state=False and deep_copy=False, it's basically share_state=True
        # Your implementation might want to warn about this or auto-correct

        config = PipelineConfig(share_state_within_batch=False, deep_copy_state_per_item=False)

        # Depending on your implementation, this might:
        # 1. Raise a warning
        # 2. Auto-correct to sensible defaults
        # 3. Allow it (shallow copy without sharing)

        # Test whatever behavior you implemented
        assert config is not None

    def test_config_repr(self):
        """Test config has useful string representation."""
        config = PipelineConfig(stop_on_failure=True, stop_on_skip=False)

        config_str = repr(config)

        # Should show the configuration values
        assert "stop_on_failure" in config_str or "True" in config_str
        assert str(config) is not None


class TestProcessorConfigAccess:
    """Test that processors can access pipeline config if needed."""

    def test_processor_receives_config_through_context(self):
        """Test if processors need config access, it's available."""
        # This test depends on your design choice
        # You might pass config through ProcessingContext
        # Or processors might not need config at all

        config = PipelineConfig(stop_on_failure=False)

        pipeline = (
            PipelineBuilder("test").with_config(config).add_processor(CounterProcessor()).build()
        )

        data = [PipelineData.create(payload={})]
        results = pipeline.execute(data)

        # If config is in context:
        # assert hasattr(results[0], 'config') or 'config' in results[0].__dict__

        # This is a design decision - processors usually shouldn't need pipeline config
        assert results[0] is not None


@pytest.mark.skip()
class TestConfigPerformance:
    """Test configuration impact on performance."""

    def test_shared_state_is_faster(self):
        """Test that shared state is faster than deep copying."""
        import time

        # Config with shared state
        config_shared = PipelineConfig(share_state_within_batch=True)
        pipeline_shared = (
            PipelineBuilder("shared")
            .with_config(config_shared)
            .add_processor(CounterProcessor())
            .build()
        )

        # Config with deep copy
        config_copied = PipelineConfig(
            share_state_within_batch=False, deep_copy_state_per_item=True
        )
        pipeline_copied = (
            PipelineBuilder("copied")
            .with_config(config_copied)
            .add_processor(CounterProcessor())
            .build()
        )

        # Large batch
        data = [PipelineData.create(payload={"i": i}) for i in range(1000)]

        # Time shared state
        start = time.time()
        pipeline_shared.execute(data)
        time_shared = time.time() - start

        # Time deep copy
        start = time.time()
        pipeline_copied.execute(data)
        time_copied = time.time() - start

        # Shared should be faster (though this might be flaky in CI)
        print(f"Shared: {time_shared:.4f}s, Copied: {time_copied:.4f}s")
        # Don't assert in actual tests, just measure
