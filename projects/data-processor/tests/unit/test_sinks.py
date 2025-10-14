"""Tests for data sinks."""

import pytest
from pipeline_framework.core.models import PipelineData, ProcessingContext
from pipeline_framework.sinks.memory import ConsoleSink, MemorySink


class TestMemorySink:
    """Test MemorySink."""

    def test_write_stores_data(self):
        """Test writing data to memory sink."""
        sink = MemorySink()

        contexts = [
            ProcessingContext(data=PipelineData.create(payload={"v": 1}), state={}),
            ProcessingContext(data=PipelineData.create(payload={"v": 2}), state={}),
        ]

        sink.write(contexts)

        results = sink.get_results()
        assert len(results) == 2
        assert results[0].data.payload["v"] == 1

    def test_write_single(self):
        """Test writing single item."""
        sink = MemorySink()

        context = ProcessingContext(data=PipelineData.create(payload={"value": 42}), state={})

        sink.write_single(context)

        results = sink.get_results()
        assert len(results) == 1
        assert results[0].data.payload["value"] == 42

    def test_multiple_writes_accumulate(self):
        """Test that multiple writes accumulate results."""
        sink = MemorySink()

        sink.write_single(ProcessingContext(data=PipelineData.create(payload={"v": 1}), state={}))
        sink.write_single(ProcessingContext(data=PipelineData.create(payload={"v": 2}), state={}))

        results = sink.get_results()
        assert len(results) == 2

    def test_write_after_close_raises_error(self):
        """Test that writing after close raises error."""
        sink = MemorySink()
        sink.close()

        with pytest.raises(RuntimeError):
            sink.write([])

    def test_get_results_after_close_works(self):
        """Test that results are still accessible after close."""
        sink = MemorySink()

        context = ProcessingContext(data=PipelineData.create(payload={}), state={})
        sink.write_single(context)
        sink.close()

        results = sink.get_results()
        assert len(results) == 1

    def test_context_manager(self):
        """Test using sink as context manager."""
        contexts = [ProcessingContext(data=PipelineData.create(payload={}), state={})]

        with MemorySink() as sink:
            sink.write(contexts)
            results = sink.get_results()
            assert len(results) == 1


class TestConsoleSink:
    """Test ConsoleSink."""

    def test_write_prints_to_console(self, capsys):
        """Test that write prints to console."""
        sink = ConsoleSink(verbose=False)

        contexts = [
            ProcessingContext(
                data=PipelineData(id="1", payload={"v": 1}, metadata={}, timestamp=None), state={}
            ),
        ]

        sink.write(contexts)

        captured = capsys.readouterr()
        assert "1" in captured.out  # ID should be in output

    def test_verbose_mode_prints_more_detail(self, capsys):
        """Test that verbose mode prints full details."""
        sink = ConsoleSink(verbose=True)

        context = ProcessingContext(
            data=PipelineData.create(payload={"name": "test", "value": 42}), state={"count": 1}
        )

        sink.write_single(context)

        captured = capsys.readouterr()
        assert "name" in captured.out or "test" in captured.out
        assert "42" in captured.out or "value" in captured.out

    def test_close_prints_summary(self, capsys):
        """Test that close prints summary."""
        sink = ConsoleSink()

        contexts = [
            ProcessingContext(data=PipelineData.create(payload={}), state={}) for _ in range(5)
        ]

        sink.write(contexts)
        sink.close()

        captured = capsys.readouterr()
        assert "5" in captured.out  # Should mention count


class TestMemorySinkEdgeCases:
    """Edge cases for MemorySink."""

    def test_write_empty_list(self):
        """Test writing empty list."""
        sink = MemorySink()

        sink.write([])

        assert len(sink.get_results()) == 0

    def test_write_and_write_single_mixed(self):
        """Test mixing write() and write_single() calls."""
        sink = MemorySink()

        sink.write([ProcessingContext(data=PipelineData.create(payload={}), state={})])
        sink.write_single(ProcessingContext(data=PipelineData.create(payload={}), state={}))
        sink.write(
            [
                ProcessingContext(data=PipelineData.create(payload={}), state={}),
                ProcessingContext(data=PipelineData.create(payload={}), state={}),
            ]
        )

        assert len(sink.get_results()) == 4

    def test_results_order_preserved(self):
        """Test that results maintain insertion order."""
        sink = MemorySink()

        contexts = [
            ProcessingContext(
                data=PipelineData(id=str(i), payload={"order": i}, metadata={}, timestamp=None),
                state={},
            )
            for i in range(10)
        ]

        for ctx in contexts:
            sink.write_single(ctx)

        results = sink.get_results()
        assert [int(r.data.id) for r in results] == list(range(10))

    def test_get_results_returns_same_list(self):
        """Test that get_results returns the actual list (not a copy)."""
        sink = MemorySink()

        ctx = ProcessingContext(data=PipelineData.create(payload={}), state={})
        sink.write_single(ctx)

        results1 = sink.get_results()
        results2 = sink.get_results()

        # Should be the same list object
        assert results1 is results2


class TestConsoleSinkEdgeCases:
    """Edge cases for ConsoleSink."""

    def test_skip_status_displayed_correctly(self, capsys):
        """Test that SKIP status is displayed correctly."""
        sink = ConsoleSink(verbose=False)

        context = ProcessingContext(
            data=PipelineData(id="test", payload={}, metadata={}, timestamp=None), state={}
        )
        context.mark_skip()

        sink.write_single(context)

        captured = capsys.readouterr()
        # Should show SKIP, not FAILURE
        assert "SKIP" in captured.out or "skip" in captured.out.lower()

    def test_verbose_with_error(self, capsys):
        """Test verbose output with error."""
        sink = ConsoleSink(verbose=True)

        context = ProcessingContext(
            data=PipelineData.create(payload={"test": "data"}), state={"count": 5}
        )
        context.mark_failure(ValueError("Test error"))

        sink.write_single(context)

        captured = capsys.readouterr()
        # Should contain useful information
        assert len(captured.out) > 50  # Substantial output

    def test_close_when_no_writes(self, capsys):
        """Test closing sink without any writes."""
        sink = ConsoleSink()

        sink.close()

        captured = capsys.readouterr()
        assert "0" in captured.out  # Should show 0 items

    def test_close_is_idempotent(self, capsys):
        """Test that calling close multiple times is safe."""
        sink = ConsoleSink()

        sink.write_single(ProcessingContext(data=PipelineData.create(payload={}), state={}))

        sink.close()
        sink.close()  # Should not print summary again
        sink.close()

        captured = capsys.readouterr()
        # Should only see one summary
        assert captured.out.count("closed") == 1
