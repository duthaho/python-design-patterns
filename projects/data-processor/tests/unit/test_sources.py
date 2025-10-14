"""Tests for data sources."""

import pytest
from pipeline_framework.core.models import PipelineData
from pipeline_framework.sources.memory import (ListSource, MemorySource,
                                               MemoryStreamSource)


class TestMemorySource:
    """Test MemorySource."""

    def test_read_returns_data(self):
        """Test reading data from memory source."""
        data = [
            PipelineData.create(payload={"value": 1}),
            PipelineData.create(payload={"value": 2}),
        ]
        source = MemorySource(data)

        result = source.read()

        assert len(result) == 2
        assert result[0].payload["value"] == 1
        assert result[1].payload["value"] == 2

    def test_read_after_close_raises_error(self):
        """Test that reading after close raises error."""
        data = [PipelineData.create(payload={})]
        source = MemorySource(data)

        source.close()

        with pytest.raises(RuntimeError):
            source.read()

    def test_context_manager(self):
        """Test using source as context manager."""
        data = [PipelineData.create(payload={"value": 1})]

        with MemorySource(data) as source:
            result = source.read()
            assert len(result) == 1

        # Source should be closed after context
        with pytest.raises(RuntimeError):
            source.read()

    def test_empty_source(self):
        """Test reading from empty source."""
        source = MemorySource([])

        result = source.read()

        assert result == []


class TestListSource:
    """Test ListSource."""

    def test_converts_dicts_to_pipeline_data(self):
        """Test converting raw dictionaries to PipelineData."""
        raw_data = [
            {"id": "1", "name": "Alice", "age": 30},
            {"id": "2", "name": "Bob", "age": 25},
        ]
        source = ListSource(raw_data)

        result = source.read()

        assert len(result) == 2
        assert result[0].id == "1"
        assert result[0].payload == {"id": "1", "name": "Alice", "age": 30}

    def test_generates_id_if_missing(self):
        """Test ID generation when id_field is missing."""
        raw_data = [
            {"name": "Alice"},
            {"name": "Bob"},
        ]
        source = ListSource(raw_data, id_field="id")

        result = source.read()

        assert len(result) == 2
        assert result[0].id is not None
        assert result[1].id is not None
        assert result[0].id != result[1].id  # IDs should be unique

    def test_custom_id_field(self):
        """Test using custom field as ID."""
        raw_data = [
            {"user_id": "u1", "name": "Alice"},
            {"user_id": "u2", "name": "Bob"},
        ]
        source = ListSource(raw_data, id_field="user_id")

        result = source.read()

        assert result[0].id == "u1"
        assert result[1].id == "u2"


class TestMemoryStreamSource:
    """Test MemoryStreamSource."""

    def test_iterates_over_data(self):
        """Test streaming data one at a time."""
        data = [PipelineData.create(payload={"value": i}) for i in range(5)]
        source = MemoryStreamSource(data)

        result = list(source)

        assert len(result) == 5
        assert all(isinstance(item, PipelineData) for item in result)

    def test_read_consumes_iterator(self):
        """Test that read() returns all data."""
        data = [PipelineData.create(payload={"value": i}) for i in range(3)]
        source = MemoryStreamSource(data)

        result = source.read()

        assert len(result) == 3

    def test_can_iterate_multiple_times(self):
        """Test that source can be iterated multiple times."""
        data = [PipelineData.create(payload={"value": i}) for i in range(3)]
        source = MemoryStreamSource(data)

        result1 = list(source)
        result2 = list(source)

        assert len(result1) == 3
        assert len(result2) == 3

    def test_iterator_after_close_raises_error(self):
        """Test that iterating after close raises error."""
        data = [PipelineData.create(payload={})]
        source = MemoryStreamSource(data)

        source.close()

        with pytest.raises(RuntimeError):
            list(source)


class TestMemorySourceEdgeCases:
    """Edge cases for MemorySource."""

    def test_reading_original_vs_copy(self):
        """Test whether read() returns a copy or original."""
        data = [PipelineData.create(payload={"value": 1})]
        source = MemorySource(data)

        result = source.read()
        result.append(PipelineData.create(payload={"value": 2}))

        # Depending on your implementation:
        # If returning original: len(data) == 2
        # If returning copy: len(data) == 1

        # Document which behavior you chose
        print(f"Original data length: {len(data)}")
        print(f"Result length: {len(result)}")

    def test_multiple_reads_allowed(self):
        """Test that source can be read multiple times."""
        data = [PipelineData.create(payload={"value": 1})]
        source = MemorySource(data)

        result1 = source.read()
        result2 = source.read()

        assert len(result1) == 1
        assert len(result2) == 1

    def test_close_is_idempotent(self):
        """Test that calling close multiple times is safe."""
        source = MemorySource([])

        source.close()
        source.close()  # Should not raise error
        source.close()

        # But reading should still fail
        with pytest.raises(RuntimeError):
            source.read()


class TestListSourceEdgeCases:
    """Edge cases for ListSource."""

    def test_empty_dict_list(self):
        """Test with list of empty dictionaries."""
        raw_data = [{}, {}, {}]
        source = ListSource(raw_data)

        result = source.read()

        assert len(result) == 3
        assert all(item.id is not None for item in result)

    def test_id_field_with_none_value(self):
        """Test when id field exists but has None value."""
        raw_data = [{"id": None, "name": "test"}]
        source = ListSource(raw_data, id_field="id")

        result = source.read()

        # Should generate ID since value is None
        assert result[0].id is not None
        assert result[0].id != "None"

    def test_id_field_with_numeric_value(self):
        """Test when ID is a number."""
        raw_data = [{"id": 123, "name": "test"}]
        source = ListSource(raw_data, id_field="id")

        result = source.read()

        # Should convert to string
        assert result[0].id == 123 or result[0].id == "123"
        assert result[0].payload == {"id": 123, "name": "test"}

    def test_complex_nested_payload(self):
        """Test with nested dictionaries and lists."""
        raw_data = [
            {
                "id": "1",
                "user": {"name": "Alice", "age": 30},
                "tags": ["python", "coding"],
                "metadata": {"created": "2024-01-01"},
            }
        ]
        source = ListSource(raw_data)

        result = source.read()

        assert result[0].payload["user"]["name"] == "Alice"
        assert "python" in result[0].payload["tags"]

    def test_duplicate_ids_allowed(self):
        """Test that duplicate IDs are preserved (not deduplicated)."""
        raw_data = [
            {"id": "same", "value": 1},
            {"id": "same", "value": 2},
        ]
        source = ListSource(raw_data)

        result = source.read()

        assert len(result) == 2
        assert result[0].id == result[1].id


class TestMemoryStreamSourceEdgeCases:
    """Edge cases for MemoryStreamSource."""

    def test_empty_stream(self):
        """Test streaming empty data."""
        source = MemoryStreamSource([])

        result = list(source)

        assert result == []

    def test_iterator_consumption(self):
        """Test that iterator can be consumed multiple times."""
        data = [PipelineData.create(payload={"value": i}) for i in range(3)]
        source = MemoryStreamSource(data)

        # First consumption
        list1 = list(source)

        # Second consumption - should work if not closed
        list2 = list(source)

        assert len(list1) == 3
        assert len(list2) == 3

    def test_partial_iteration(self):
        """Test partial iteration doesn't affect future iterations."""
        data = [PipelineData.create(payload={"value": i}) for i in range(5)]
        source = MemoryStreamSource(data)

        # Partial iteration
        iterator = iter(source)
        item1 = next(iterator)
        item2 = next(iterator)

        # Full iteration - should get all items
        full_list = list(source)

        assert len(full_list) == 5

    def test_use_in_for_loop(self):
        """Test using source directly in for loop."""
        data = [PipelineData.create(payload={"value": i}) for i in range(3)]
        source = MemoryStreamSource(data)

        count = 0
        for item in source:
            count += 1
            assert isinstance(item, PipelineData)

        assert count == 3
