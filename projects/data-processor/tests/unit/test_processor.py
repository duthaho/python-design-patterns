"""Tests for processor base class."""

from pipeline_framework.core.models import PipelineData, ProcessingContext
from pipeline_framework.core.processor import Processor


class SimpleProcessor(Processor):
    """Simple test processor that adds a value to state."""

    def _do_process(self, context: ProcessingContext) -> ProcessingContext:
        count = context.state.get("count", 0)
        context.state["count"] = count + 1
        return context


class FailingProcessor(Processor):
    """Processor that always fails."""

    def _do_process(self, context: ProcessingContext) -> ProcessingContext:
        raise ValueError("Intentional failure")


class ConditionalProcessor(Processor):
    """Processor that only processes even counts."""

    def _should_process(self, context: ProcessingContext) -> bool:
        if not super()._should_process(context):
            return False
        count = context.state.get("count", 0)
        return count % 2 == 0

    def _do_process(self, context: ProcessingContext) -> ProcessingContext:
        context.data.add_metadata("processed_by", "ConditionalProcessor")
        return context


class TestProcessor:
    """Test Processor base class."""

    def test_processor_has_name(self):
        """Test processor has a name."""
        processor = SimpleProcessor()
        assert processor.name == "SimpleProcessor"

        processor_with_name = SimpleProcessor(name="CustomName")
        assert processor_with_name.name == "CustomName"

    def test_set_next_returns_next_processor(self):
        """Test set_next returns the processor for chaining."""
        proc1 = SimpleProcessor()
        proc2 = SimpleProcessor()
        proc3 = SimpleProcessor()

        result = proc1.set_next(proc2).set_next(proc3)

        assert result == proc3

    def test_single_processor_processes_data(self):
        """Test single processor can process data."""
        processor = SimpleProcessor()
        data = PipelineData.create(payload={"value": 1})
        context = ProcessingContext(data=data, state={})

        result = processor.process(context)

        assert result.state["count"] == 1
        assert result.is_success()
        assert "SimpleProcessor" in result.processing_history

    def test_chain_of_processors(self):
        """Test chain of responsibility pattern."""
        proc1 = SimpleProcessor(name="Proc1")
        proc2 = SimpleProcessor(name="Proc2")
        proc3 = SimpleProcessor(name="Proc3")

        proc1.set_next(proc2).set_next(proc3)

        data = PipelineData.create(payload={})
        context = ProcessingContext(data=data, state={})

        result = proc1.process(context)

        assert result.state["count"] == 3
        assert result.processing_history == ["Proc1", "Proc2", "Proc3"]

    def test_processor_handles_errors(self):
        """Test error handling in processor."""
        processor = FailingProcessor()
        data = PipelineData.create(payload={})
        context = ProcessingContext(data=data, state={})

        result = processor.process(context)

        assert result.is_failure()
        assert result.error is not None
        assert isinstance(result.error, ValueError)
        assert str(result.error) == "Intentional failure"

    def test_chain_stops_on_failure(self):
        """Test that chain stops processing on failure by default."""
        proc1 = SimpleProcessor(name="Proc1")
        proc2 = FailingProcessor(name="FailProc")
        proc3 = SimpleProcessor(name="Proc3")

        proc1.set_next(proc2).set_next(proc3)

        data = PipelineData.create(payload={})
        context = ProcessingContext(data=data, state={})

        result = proc1.process(context)

        # Count should be 1 (only Proc1 processed)
        assert result.state["count"] == 1
        assert result.is_failure()
        # Proc3 should not process but still be in history (passed through)
        assert "Proc1" in result.processing_history
        assert "FailProc" in result.processing_history
        assert "Proc3" in result.processing_history

    def test_conditional_processing(self):
        """Test conditional processor with _should_process."""
        counter = SimpleProcessor(name="Counter")
        conditional = ConditionalProcessor(name="Conditional")

        counter.set_next(conditional)

        # First run: count=1 (odd), conditional should not process
        data1 = PipelineData.create(payload={})
        context1 = ProcessingContext(data=data1, state={})
        result1 = counter.process(context1)

        assert result1.state["count"] == 1
        assert "processed_by" not in result1.data.metadata

        # Second run: count=2 (even), conditional should process
        data2 = PipelineData.create(payload={})
        context2 = ProcessingContext(data=data2, state=result1.state)
        result2 = counter.process(context2)

        assert result2.state["count"] == 2
        assert result2.data.metadata.get("processed_by") == "ConditionalProcessor"
