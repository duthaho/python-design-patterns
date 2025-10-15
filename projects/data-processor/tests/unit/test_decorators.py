"""Tests for processor decorators."""

import time

from pipeline_framework.core.models import PipelineData, ProcessingContext
from pipeline_framework.core.processor import Processor
from pipeline_framework.decorators.caching import CachingDecorator
from pipeline_framework.decorators.logging import LoggingDecorator
from pipeline_framework.decorators.retry import RetryDecorator
from pipeline_framework.decorators.timing import TimingDecorator


class SimpleProcessor(Processor):
    """Simple processor for testing."""

    def _do_process(self, context: ProcessingContext) -> ProcessingContext:
        context.data.set_payload_value("processed", True)
        return context


class FailingProcessor(Processor):
    """Processor that fails a certain number of times."""

    def __init__(self, fail_count: int = 2):
        super().__init__()
        self.attempts = 0
        self.fail_count = fail_count

    def _do_process(self, context: ProcessingContext) -> ProcessingContext:
        self.attempts += 1
        if self.attempts <= self.fail_count:
            raise ValueError(f"Attempt {self.attempts} failed")
        return context


class TestRetryDecorator:
    """Test RetryDecorator."""

    def test_retry_succeeds_eventually(self):
        """Test that retry succeeds after failures."""
        processor = FailingProcessor(fail_count=2)
        retry_processor = RetryDecorator(processor, max_retries=3, retry_delay=0.01)

        data = PipelineData.create(payload={})
        context = ProcessingContext(data=data, state={})

        result = retry_processor.process(context)

        assert result.is_success()
        assert processor.attempts == 3  # Failed 2 times, succeeded on 3rd

    def test_retry_fails_after_max_attempts(self):
        """Test that retry stops after max attempts."""
        processor = FailingProcessor(fail_count=10)
        retry_processor = RetryDecorator(processor, max_retries=3, retry_delay=0.01)

        data = PipelineData.create(payload={})
        context = ProcessingContext(data=data, state={})

        result = retry_processor.process(context)

        assert result.is_failure()
        assert processor.attempts == 4  # Initial + 3 retries

    def test_retry_adds_metadata(self):
        """Test that retry adds metadata about attempts."""
        processor = FailingProcessor(fail_count=1)
        retry_processor = RetryDecorator(processor, max_retries=3, retry_delay=0.01)

        data = PipelineData.create(payload={})
        context = ProcessingContext(data=data, state={})

        result = retry_processor.process(context)

        assert "retry_count" in result.data.metadata


class TestLoggingDecorator:
    """Test LoggingDecorator."""

    def test_logging_success(self, caplog):
        """Test logging on successful processing."""
        import logging

        caplog.set_level(logging.INFO)

        processor = SimpleProcessor()
        logging_processor = LoggingDecorator(processor)

        data = PipelineData.create(payload={"value": 1})
        context = ProcessingContext(data=data, state={})

        result = logging_processor.process(context)

        assert result.is_success()
        # Check that something was logged
        assert len(caplog.records) > 0

    def test_logging_failure(self, caplog):
        """Test logging on processing failure."""
        import logging

        caplog.set_level(logging.ERROR)

        processor = FailingProcessor(fail_count=10)
        logging_processor = LoggingDecorator(processor)

        data = PipelineData.create(payload={})
        context = ProcessingContext(data=data, state={})

        result = logging_processor.process(context)

        assert result.is_failure()
        # Check that error was logged
        assert any("failed" in record.message.lower() for record in caplog.records)


class TestCachingDecorator:
    """Test CachingDecorator."""

    def test_cache_hit(self):
        """Test cache hit on second call with same data."""
        processor = SimpleProcessor()
        caching_processor = CachingDecorator(processor)

        data = PipelineData.create(payload={"key": "value"})
        context1 = ProcessingContext(data=data.clone(), state={})
        context2 = ProcessingContext(data=data.clone(), state={})

        # First call - cache miss
        result1 = caching_processor.process(context1)
        assert result1.data.metadata.get("cache_hit") is False

        # Second call - cache hit
        result2 = caching_processor.process(context2)
        assert result2.data.metadata.get("cache_hit") is True

    def test_cache_stats(self):
        """Test cache statistics."""
        processor = SimpleProcessor()
        caching_processor = CachingDecorator(processor)

        # Process same data multiple times
        for _ in range(5):
            data = PipelineData.create(payload={"key": "value"})
            context = ProcessingContext(data=data, state={})
            caching_processor.process(context)

        stats = caching_processor.cache_stats

        assert stats["hits"] == 4  # First miss, then 4 hits
        assert stats["misses"] == 1
        assert stats["hit_rate"] > 0.5

    def test_cache_different_data(self):
        """Test that different data doesn't hit cache."""
        processor = SimpleProcessor()
        caching_processor = CachingDecorator(processor)

        data1 = PipelineData.create(payload={"key": "value1"})
        data2 = PipelineData.create(payload={"key": "value2"})

        context1 = ProcessingContext(data=data1, state={})
        context2 = ProcessingContext(data=data2, state={})

        result1 = caching_processor.process(context1)
        result2 = caching_processor.process(context2)

        # Both should be cache misses
        assert result1.data.metadata.get("cache_hit") is False
        assert result2.data.metadata.get("cache_hit") is False

    def test_clear_cache(self):
        """Test clearing the cache."""
        processor = SimpleProcessor()
        caching_processor = CachingDecorator(processor)

        data = PipelineData.create(payload={"key": "value"})
        context = ProcessingContext(data=data, state={})

        caching_processor.process(context)
        caching_processor.clear_cache()

        stats = caching_processor.cache_stats
        assert stats["cache_size"] == 0
        assert stats["hits"] == 0


class TestTimingDecorator:
    """Test TimingDecorator."""

    def test_timing_measurement(self):
        """Test that timing is measured."""

        class SlowProcessor(Processor):
            def _do_process(self, context):
                time.sleep(0.1)  # Sleep for 100ms
                return context

        processor = SlowProcessor()
        timing_processor = TimingDecorator(processor)

        data = PipelineData.create(payload={})
        context = ProcessingContext(data=data, state={})

        result = timing_processor.process(context)

        # Check timing was recorded in metadata
        assert "processing_time_ms" in result.data.metadata
        assert result.data.metadata["processing_time_ms"] >= 100

    def test_timing_stats(self):
        """Test timing statistics."""
        processor = SimpleProcessor()
        timing_processor = TimingDecorator(processor)

        # Process multiple items
        for _ in range(5):
            data = PipelineData.create(payload={})
            context = ProcessingContext(data=data, state={})
            timing_processor.process(context)

        stats = timing_processor.timing_stats

        assert stats["call_count"] == 5
        assert stats["avg_time"] > 0
        assert stats["min_time"] <= stats["avg_time"] <= stats["max_time"]

    def test_reset_stats(self):
        """Test resetting timing statistics."""
        processor = SimpleProcessor()
        timing_processor = TimingDecorator(processor)

        data = PipelineData.create(payload={})
        context = ProcessingContext(data=data, state={})
        timing_processor.process(context)

        timing_processor.reset_stats()

        stats = timing_processor.timing_stats
        assert stats["call_count"] == 0


class TestDecoratorStacking:
    """Test stacking multiple decorators."""

    def test_stack_retry_and_logging(self):
        """Test combining retry and logging decorators."""
        processor = FailingProcessor(fail_count=1)
        decorated = RetryDecorator(LoggingDecorator(processor), max_retries=3, retry_delay=0.01)

        data = PipelineData.create(payload={})
        context = ProcessingContext(data=data, state={})

        result = decorated.process(context)

        assert result.is_success()

    def test_stack_timing_caching_logging(self):
        """Test combining timing, caching, and logging."""
        processor = SimpleProcessor()
        decorated = TimingDecorator(CachingDecorator(LoggingDecorator(processor)))

        data = PipelineData.create(payload={"key": "value"})

        # First call
        context1 = ProcessingContext(data=data.clone(), state={})
        result1 = decorated.process(context1)

        # Second call (should hit cache and be faster)
        context2 = ProcessingContext(data=data.clone(), state={})
        result2 = decorated.process(context2)

        assert result1.is_success()
        assert result2.is_success()
