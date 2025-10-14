"""Tests for file sinks."""

import csv
import json

import pytest
from pipeline_framework.core.models import PipelineData, ProcessingContext
from pipeline_framework.sinks.file import CSVFileSink, JSONFileSink


class TestCSVFileSink:
    """Test CSVFileSink."""

    def test_write_creates_file(self, tmp_path):
        """Test that write creates CSV file."""
        csv_file = tmp_path / "output.csv"

        sink = CSVFileSink(str(csv_file))
        contexts = [
            ProcessingContext(
                data=PipelineData.create(payload={"name": "Alice", "age": 30}), state={}
            ),
            ProcessingContext(
                data=PipelineData.create(payload={"name": "Bob", "age": 25}), state={}
            ),
        ]

        sink.write(contexts)
        sink.close()

        assert csv_file.exists()

        # Verify content
        with open(csv_file, "r") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 2
            assert rows[0]["name"] == "Alice"

    def test_write_with_header(self, tmp_path):
        """Test writing CSV with header."""
        csv_file = tmp_path / "output.csv"

        sink = CSVFileSink(str(csv_file), write_header=True)
        sink.write(
            [
                ProcessingContext(
                    data=PipelineData.create(payload={"id": "1", "value": "test"}), state={}
                )
            ]
        )
        sink.close()

        with open(csv_file, "r") as f:
            content = f.read()
            assert "id" in content
            assert "value" in content

    def test_append_mode(self, tmp_path):
        """Test appending to existing CSV."""
        csv_file = tmp_path / "output.csv"

        # First write
        sink1 = CSVFileSink(str(csv_file), mode="w")
        sink1.write(
            [ProcessingContext(data=PipelineData.create(payload={"name": "Alice"}), state={})]
        )
        sink1.close()

        # Append
        sink2 = CSVFileSink(str(csv_file), mode="a", write_header=False)
        sink2.write(
            [ProcessingContext(data=PipelineData.create(payload={"name": "Bob"}), state={})]
        )
        sink2.close()

        # Verify both rows exist
        with open(csv_file, "r") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 2

    def test_write_single(self, tmp_path):
        """Test writing single context."""
        csv_file = tmp_path / "output.csv"

        sink = CSVFileSink(str(csv_file))
        sink.write_single(
            ProcessingContext(data=PipelineData.create(payload={"value": 42}), state={})
        )
        sink.close()

        assert csv_file.exists()

    def test_creates_parent_directories(self, tmp_path):
        """Test that parent directories are created."""
        csv_file = tmp_path / "subdir" / "nested" / "output.csv"

        sink = CSVFileSink(str(csv_file))
        sink.write(
            [ProcessingContext(data=PipelineData.create(payload={"test": "data"}), state={})]
        )
        sink.close()

        assert csv_file.exists()
        assert csv_file.parent.exists()

    def test_context_manager(self, tmp_path):
        """Test using sink as context manager."""
        csv_file = tmp_path / "output.csv"

        with CSVFileSink(str(csv_file)) as sink:
            sink.write(
                [ProcessingContext(data=PipelineData.create(payload={"value": 1}), state={})]
            )

        assert csv_file.exists()

    def test_write_after_close_raises_error(self, tmp_path):
        """Test writing after close raises error."""
        csv_file = tmp_path / "output.csv"

        sink = CSVFileSink(str(csv_file))
        sink.close()

        with pytest.raises(RuntimeError):
            sink.write([])


class TestJSONFileSink:
    """Test JSONFileSink."""

    def test_write_json_array(self, tmp_path):
        """Test writing JSON array format."""
        json_file = tmp_path / "output.json"

        sink = JSONFileSink(str(json_file), json_lines=False)
        contexts = [
            ProcessingContext(
                data=PipelineData.create(payload={"name": "Alice", "age": 30}), state={}
            ),
            ProcessingContext(
                data=PipelineData.create(payload={"name": "Bob", "age": 25}), state={}
            ),
        ]

        sink.write(contexts)
        sink.close()

        assert json_file.exists()

        # Verify content
        with open(json_file, "r") as f:
            data = json.load(f)
            assert isinstance(data, list)
            assert len(data) == 2

    def test_write_json_lines(self, tmp_path):
        """Test writing JSON Lines format."""
        json_file = tmp_path / "output.jsonl"

        sink = JSONFileSink(str(json_file), json_lines=True)
        contexts = [
            ProcessingContext(
                data=PipelineData.create(payload={"id": "1", "name": "Alice"}), state={}
            ),
            ProcessingContext(
                data=PipelineData.create(payload={"id": "2", "name": "Bob"}), state={}
            ),
        ]

        sink.write(contexts)
        sink.close()

        # Verify JSON Lines format
        with open(json_file, "r") as f:
            lines = f.readlines()
            assert len(lines) == 2
            obj1 = json.loads(lines[0])
            obj2 = json.loads(lines[1])
            assert obj1.get("id") == "1" or "Alice" in str(obj1)
            assert obj2.get("id") == "2" or "Bob" in str(obj2)

    def test_pretty_printing(self, tmp_path):
        """Test JSON pretty printing."""
        json_file = tmp_path / "output.json"

        sink = JSONFileSink(str(json_file), indent=4)
        sink.write(
            [ProcessingContext(data=PipelineData.create(payload={"name": "Alice"}), state={})]
        )
        sink.close()

        with open(json_file, "r") as f:
            content = f.read()
            # Pretty printed JSON has newlines and spaces
            assert "\n" in content

    def test_compact_json(self, tmp_path):
        """Test compact JSON (no indentation)."""
        json_file = tmp_path / "output.json"

        sink = JSONFileSink(str(json_file), indent=None)
        sink.write(
            [ProcessingContext(data=PipelineData.create(payload={"name": "Alice"}), state={})]
        )
        sink.close()

        assert json_file.exists()

    def test_nested_structures(self, tmp_path):
        """Test writing nested structures."""
        json_file = tmp_path / "output.json"

        sink = JSONFileSink(str(json_file))
        sink.write(
            [
                ProcessingContext(
                    data=PipelineData.create(
                        payload={
                            "user": {"name": "Alice", "email": "alice@example.com"},
                            "scores": [85, 90, 95],
                            "metadata": {"verified": True},
                        }
                    ),
                    state={},
                )
            ]
        )
        sink.close()

        with open(json_file, "r") as f:
            data = json.load(f)
            assert isinstance(data, list)

    def test_write_single(self, tmp_path):
        """Test writing single context."""
        json_file = tmp_path / "output.json"

        sink = JSONFileSink(str(json_file))
        sink.write_single(
            ProcessingContext(data=PipelineData.create(payload={"value": 42}), state={})
        )
        sink.close()

        assert json_file.exists()

    def test_creates_parent_directories(self, tmp_path):
        """Test parent directory creation."""
        json_file = tmp_path / "deep" / "nested" / "output.json"

        sink = JSONFileSink(str(json_file))
        sink.write(
            [ProcessingContext(data=PipelineData.create(payload={"test": "data"}), state={})]
        )
        sink.close()

        assert json_file.exists()
