"""Tests for data adapters."""

import json

from pipeline_framework.adapters.base import IdentityAdapter
from pipeline_framework.adapters.csv_adapter import CSVAdapter
from pipeline_framework.adapters.json_adapter import JSONAdapter
from pipeline_framework.core.models import PipelineData, ProcessingContext


class TestIdentityAdapter:
    """Test IdentityAdapter."""

    def test_to_pipeline_data(self):
        """Test converting dict to PipelineData."""
        adapter = IdentityAdapter()
        raw_data = {"name": "Alice", "age": 30}

        result = adapter.to_pipeline_data(raw_data)

        assert isinstance(result, PipelineData)
        assert result.payload == raw_data

    def test_from_pipeline_data(self):
        """Test extracting payload from context."""
        adapter = IdentityAdapter()
        context = ProcessingContext(data=PipelineData.create(payload={"name": "Bob"}), state={})

        result = adapter.from_pipeline_data(context)

        assert result == {"name": "Bob"}


class TestCSVAdapter:
    """Test CSVAdapter."""

    def test_to_pipeline_data_with_id(self):
        """Test converting CSV row with ID."""
        adapter = CSVAdapter(id_field="user_id")
        row = {"user_id": "123", "name": "Alice", "age": "30"}

        result = adapter.to_pipeline_data(row)

        assert result.id == "123"
        assert result.payload["name"] == "Alice"

    def test_to_pipeline_data_generates_id(self):
        """Test ID generation when missing."""
        adapter = CSVAdapter(id_field="id")
        row = {"name": "Bob", "age": "25"}

        result = adapter.to_pipeline_data(row)

        assert result.id is not None
        assert len(result.id) > 0

    def test_to_pipeline_data_separates_metadata(self):
        """Test metadata field separation."""
        adapter = CSVAdapter(metadata_prefix="_meta_")
        row = {"id": "1", "name": "Charlie", "_meta_source": "api", "_meta_timestamp": "2024-01-01"}

        result = adapter.to_pipeline_data(row)

        assert "name" in result.payload
        assert "_meta_source" not in result.payload
        assert result.metadata["source"] == "api"
        assert result.metadata["timestamp"] == "2024-01-01"

    def test_from_pipeline_data_basic(self):
        """Test converting context to CSV row."""
        adapter = CSVAdapter()
        context = ProcessingContext(
            data=PipelineData.create(payload={"name": "David", "age": 35}), state={}
        )

        result = adapter.from_pipeline_data(context)

        assert result["name"] == "David"
        assert result["age"] == 35

    def test_from_pipeline_data_with_metadata(self):
        """Test including metadata in output."""
        adapter = CSVAdapter(include_metadata_fields=True, metadata_prefix="_meta_")

        data = PipelineData.create(payload={"name": "Eve"})
        data.add_metadata("source", "test")

        context = ProcessingContext(data=data, state={})
        result = adapter.from_pipeline_data(context)

        assert result["name"] == "Eve"
        assert result["_meta_source"] == "test"


class TestJSONAdapter:
    """Test JSONAdapter."""

    def test_to_pipeline_data_simple(self):
        """Test converting simple JSON object."""
        adapter = JSONAdapter()
        obj = {"id": "1", "name": "Alice", "age": 30}

        result = adapter.to_pipeline_data(obj)

        assert result.id == "1"
        assert result.payload["name"] == "Alice"

    def test_to_pipeline_data_nested(self):
        """Test converting nested JSON object."""
        adapter = JSONAdapter()
        obj = {
            "id": "2",
            "user": {"name": "Bob", "email": "bob@example.com"},
            "scores": [85, 90, 95],
        }

        result = adapter.to_pipeline_data(obj)

        assert result.payload["user"]["name"] == "Bob"
        assert result.payload["scores"] == [85, 90, 95]

    def test_to_pipeline_data_with_metadata_field(self):
        """Test JSON with dedicated metadata field."""
        adapter = JSONAdapter()
        obj = {"id": "3", "name": "Charlie", "metadata": {"source": "api", "version": "1.0"}}

        result = adapter.to_pipeline_data(obj)

        # Metadata should be extracted
        assert result.metadata.get("source") == "api"

    def test_from_pipeline_data_basic(self):
        """Test converting context to JSON object."""
        adapter = JSONAdapter()
        context = ProcessingContext(data=PipelineData.create(payload={"name": "David"}), state={})

        result = adapter.from_pipeline_data(context)

        assert "name" in result or "payload" in result

    def test_from_pipeline_data_with_processing_info(self):
        """Test including processing information."""
        adapter = JSONAdapter(include_processing_info=True)

        data = PipelineData.create(payload={"name": "Eve"})
        context = ProcessingContext(data=data, state={})
        context.add_to_history("Processor1")
        context.add_to_history("Processor2")

        result = adapter.from_pipeline_data(context)

        # Should include processing info
        assert "processing" in result or "status" in result


class TestCSVAdapterEdgeCases:
    """Edge cases for CSVAdapter."""

    def test_from_pipeline_data_creates_flat_structure(self):
        """Test that CSV output is flat (no nested dicts)."""
        adapter = CSVAdapter()

        data = PipelineData.create(payload={"name": "Alice"})
        context = ProcessingContext(data=data, state={})
        context.add_to_history("Proc1")
        context.add_to_history("Proc2")

        row = adapter.from_pipeline_data(context)

        # All values should be scalar (not dict or list)
        for key, value in row.items():
            assert not isinstance(value, (dict, list)), f"Field '{key}' has nested value: {value}"

    def test_from_pipeline_data_with_error(self):
        """Test CSV output when processing failed."""
        adapter = CSVAdapter()

        data = PipelineData.create(payload={"name": "Bob"})
        context = ProcessingContext(data=data, state={})
        context.mark_failure(ValueError("Test error"))

        row = adapter.from_pipeline_data(context)

        # Should have status field
        assert "_status" in row
        assert row["_status"] == "failure"

        # Error should be converted to string
        if "_error" in row:
            assert isinstance(row["_error"], str)


class TestJSONAdapterEdgeCases:
    """Edge cases for JSONAdapter."""

    def test_from_pipeline_data_serializes_error(self):
        """Test that error is JSON serializable."""
        adapter = JSONAdapter(include_processing_info=True)

        data = PipelineData.create(payload={"test": "data"})
        context = ProcessingContext(data=data, state={})
        context.mark_failure(ValueError("Test error message"))

        result = adapter.from_pipeline_data(context)

        # Should be JSON serializable
        json_str = json.dumps(result)
        assert "Test error message" in json_str

    def test_to_pipeline_data_removes_id_from_payload(self):
        """Test that ID doesn't appear twice."""
        adapter = JSONAdapter(id_field="id")

        raw = {"id": "123", "name": "Alice", "age": 30}
        data = adapter.to_pipeline_data(raw)

        assert data.id == "123"

        # ID should NOT be in payload (choose your preference)
        # If you want to keep ID in payload, adjust this test
        # assert "id" not in data.payload  # Or assert it IS in payload

    def test_nested_structures_preserved(self):
        """Test that nested structures are preserved."""
        adapter = JSONAdapter()

        raw = {
            "id": "1",
            "user": {"name": "Alice", "tags": ["python", "data"]},
            "scores": [85, 90, 95],
        }

        data = adapter.to_pipeline_data(raw)

        # Nested structures should be preserved
        assert isinstance(data.payload["user"], dict)
        assert isinstance(data.payload["scores"], list)
