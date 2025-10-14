"""Tests for file sources."""

import csv
import json
import tempfile
from pathlib import Path

import pytest
from pipeline_framework.core.models import PipelineData
from pipeline_framework.sources.file import (CSVFileSource, CSVStreamSource,
                                             JSONFileSource)


class TestCSVFileSource:
    """Test CSVFileSource."""

    def test_read_simple_csv(self, tmp_path):
        """Test reading a simple CSV file."""
        # Create test CSV
        csv_file = tmp_path / "test.csv"
        with open(csv_file, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["id", "name", "age"])
            writer.writeheader()
            writer.writerow({"id": "1", "name": "Alice", "age": "30"})
            writer.writerow({"id": "2", "name": "Bob", "age": "25"})

        source = CSVFileSource(str(csv_file))
        result = source.read()

        assert len(result) == 2
        assert result[0].id == "1"
        assert result[0].payload["name"] == "Alice"
        assert result[1].id == "2"

    def test_file_not_found_raises_error(self):
        """Test that missing file raises error."""
        with pytest.raises(FileNotFoundError):
            CSVFileSource("nonexistent.csv")

    def test_read_after_close(self, tmp_path):
        """Test reading after close raises error."""
        csv_file = tmp_path / "test.csv"
        with open(csv_file, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["id"])
            writer.writeheader()

        source = CSVFileSource(str(csv_file))
        source.close()

        with pytest.raises(RuntimeError):
            source.read()

    def test_context_manager(self, tmp_path):
        """Test using source as context manager."""
        csv_file = tmp_path / "test.csv"
        with open(csv_file, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["id", "value"])
            writer.writeheader()
            writer.writerow({"id": "1", "value": "test"})

        with CSVFileSource(str(csv_file)) as source:
            result = source.read()
            assert len(result) == 1


class TestJSONFileSource:
    """Test JSONFileSource."""

    def test_read_json_array(self, tmp_path):
        """Test reading JSON array format."""
        json_file = tmp_path / "test.json"
        data = [{"id": "1", "name": "Alice"}, {"id": "2", "name": "Bob"}]
        with open(json_file, "w") as f:
            json.dump(data, f)

        source = JSONFileSource(str(json_file))
        result = source.read()

        assert len(result) == 2
        assert result[0].payload["name"] == "Alice"

    def test_read_json_lines(self, tmp_path):
        """Test reading JSON Lines format."""
        json_file = tmp_path / "test.jsonl"
        with open(json_file, "w") as f:
            f.write('{"id": "1", "name": "Alice"}\n')
            f.write('{"id": "2", "name": "Bob"}\n')

        source = JSONFileSource(str(json_file), json_lines=True)
        result = source.read()

        assert len(result) == 2
        assert result[0].id == "1"
        assert result[1].payload["name"] == "Bob"

    def test_nested_json_objects(self, tmp_path):
        """Test reading JSON with nested structures."""
        json_file = tmp_path / "test.json"
        data = [
            {
                "id": "1",
                "user": {"name": "Alice", "email": "alice@example.com"},
                "tags": ["python", "data"],
            }
        ]
        with open(json_file, "w") as f:
            json.dump(data, f)

        source = JSONFileSource(str(json_file))
        result = source.read()

        assert result[0].payload["user"]["name"] == "Alice"
        assert "python" in result[0].payload["tags"]

    def test_file_not_found(self):
        """Test missing file raises error."""
        with pytest.raises(FileNotFoundError):
            JSONFileSource("nonexistent.json")


class TestCSVStreamSource:
    """Test CSVStreamSource."""

    def test_iterate_over_large_file(self, tmp_path):
        """Test streaming large CSV file."""
        csv_file = tmp_path / "large.csv"

        # Create large CSV
        with open(csv_file, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["id", "value"])
            writer.writeheader()
            for i in range(1000):
                writer.writerow({"id": str(i), "value": f"item_{i}"})

        source = CSVStreamSource(str(csv_file))

        # Stream without loading all into memory
        count = 0
        for item in source:
            count += 1
            assert isinstance(item, PipelineData)
            if count >= 10:  # Just check first 10
                break

        assert count == 10

    def test_read_consumes_iterator(self, tmp_path):
        """Test that read() loads all data."""
        csv_file = tmp_path / "test.csv"
        with open(csv_file, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["id"])
            writer.writeheader()
            for i in range(5):
                writer.writerow({"id": str(i)})

        source = CSVStreamSource(str(csv_file))
        result = source.read()

        assert len(result) == 5

    def test_multiple_iterations(self, tmp_path):
        """Test that source can be iterated multiple times."""
        csv_file = tmp_path / "test.csv"
        with open(csv_file, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["id"])
            writer.writeheader()
            for i in range(3):
                writer.writerow({"id": str(i)})

        source = CSVStreamSource(str(csv_file))

        list1 = list(source)
        list2 = list(source)

        assert len(list1) == 3
        assert len(list2) == 3
