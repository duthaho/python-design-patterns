"""Tests for core data models."""

from datetime import datetime

from pipeline_framework.core.models import (PipelineData, ProcessingContext,
                                            ProcessingResult)


class TestPipelineData:
    """Test PipelineData class."""

    def test_create_with_all_fields(self):
        """Test creating PipelineData with all fields specified."""
        timestamp = datetime.now()
        data = PipelineData(
            id="test-1",
            payload={"name": "Alice"},
            metadata={"source": "test"},
            timestamp=timestamp,
        )

        assert data.id == "test-1"
        assert data.payload == {"name": "Alice"}
        assert data.metadata == {"source": "test"}
        assert data.timestamp == timestamp

    def test_create_factory_method(self):
        """Test factory method generates ID automatically."""
        data = PipelineData.create(payload={"name": "Bob"})

        assert data.id is not None
        assert len(data.id) > 0
        assert data.payload == {"name": "Bob"}
        assert data.metadata == {}

    def test_clone_creates_deep_copy(self):
        """Test that clone creates an independent copy."""
        original = PipelineData.create(payload={"name": "Charlie", "scores": [1, 2, 3]})
        cloned = original.clone()

        # Modify cloned data
        cloned.payload["name"] = "David"
        cloned.payload["scores"].append(4)

        # Original should be unchanged
        assert original.payload["name"] == "Charlie"
        assert original.payload["scores"] == [1, 2, 3]
        assert cloned.payload["name"] == "David"
        assert cloned.payload["scores"] == [1, 2, 3, 4]

    def test_get_payload_value(self):
        """Test getting payload values."""
        data = PipelineData.create(payload={"name": "Eve", "age": 30})

        assert data.get_payload_value("name") == "Eve"
        assert data.get_payload_value("age") == 30
        assert data.get_payload_value("nonexistent") is None
        assert data.get_payload_value("nonexistent", "default") == "default"

    def test_set_payload_value(self):
        """Test setting payload values."""
        data = PipelineData.create(payload={"name": "Frank"})
        data.set_payload_value("age", 25)

        assert data.payload["age"] == 25

    def test_add_metadata(self):
        """Test adding metadata."""
        data = PipelineData.create(payload={})
        data.add_metadata("processor", "test-processor")
        data.add_metadata("timestamp", "2024-01-01")

        assert data.metadata["processor"] == "test-processor"
        assert data.metadata["timestamp"] == "2024-01-01"


class TestProcessingContext:
    """Test ProcessingContext class."""

    def test_initial_state(self):
        """Test initial context state."""
        data = PipelineData.create(payload={"test": "data"})
        context = ProcessingContext(data=data, state={})

        assert context.result == ProcessingResult.SUCCESS
        assert context.error is None
        assert context.processing_history == []

    def test_mark_success(self):
        """Test marking context as successful."""
        data = PipelineData.create(payload={})
        context = ProcessingContext(data=data, state={})
        context.mark_failure(Exception("test"))

        context.mark_success()

        assert context.result == ProcessingResult.SUCCESS
        assert context.error is None

    def test_mark_failure(self):
        """Test marking context as failed."""
        data = PipelineData.create(payload={})
        context = ProcessingContext(data=data, state={})
        error = ValueError("Test error")

        context.mark_failure(error)

        assert context.result == ProcessingResult.FAILURE
        assert context.error == error

    def test_mark_skip(self):
        """Test marking context as skipped."""
        data = PipelineData.create(payload={})
        context = ProcessingContext(data=data, state={})

        context.mark_skip()

        assert context.result == ProcessingResult.SKIP

    def test_add_to_history(self):
        """Test adding to processing history."""
        data = PipelineData.create(payload={})
        context = ProcessingContext(data=data, state={})

        context.add_to_history("Processor1")
        context.add_to_history("Processor2")

        assert context.processing_history == ["Processor1", "Processor2"]

    def test_status_checks(self):
        """Test status checking methods."""
        data = PipelineData.create(payload={})
        context = ProcessingContext(data=data, state={})

        assert context.is_success()
        assert not context.is_failure()
        assert not context.is_skip()

        context.mark_failure(Exception())
        """Tests for core data models."""


from datetime import datetime

import pytest
from pipeline_framework.core.models import (PipelineData, ProcessingContext,
                                            ProcessingResult)


class TestPipelineData:
    """Test PipelineData class."""

    def test_create_with_all_fields(self):
        """Test creating PipelineData with all fields specified."""
        timestamp = datetime.now()
        data = PipelineData(
            id="test-1",
            payload={"name": "Alice"},
            metadata={"source": "test"},
            timestamp=timestamp,
        )

        assert data.id == "test-1"
        assert data.payload == {"name": "Alice"}
        assert data.metadata == {"source": "test"}
        assert data.timestamp == timestamp

    def test_create_factory_method(self):
        """Test factory method generates ID automatically."""
        data = PipelineData.create(payload={"name": "Bob"})

        assert data.id is not None
        assert len(data.id) > 0
        assert data.payload == {"name": "Bob"}
        assert data.metadata == {}

    def test_clone_creates_deep_copy(self):
        """Test that clone creates an independent copy."""
        original = PipelineData.create(payload={"name": "Charlie", "scores": [1, 2, 3]})
        cloned = original.clone()

        # Modify cloned data
        cloned.payload["name"] = "David"
        cloned.payload["scores"].append(4)

        # Original should be unchanged
        assert original.payload["name"] == "Charlie"
        assert original.payload["scores"] == [1, 2, 3]
        assert cloned.payload["name"] == "David"
        assert cloned.payload["scores"] == [1, 2, 3, 4]

    def test_get_payload_value(self):
        """Test getting payload values."""
        data = PipelineData.create(payload={"name": "Eve", "age": 30})

        assert data.get_payload_value("name") == "Eve"
        assert data.get_payload_value("age") == 30
        assert data.get_payload_value("nonexistent") is None
        assert data.get_payload_value("nonexistent", "default") == "default"

    def test_set_payload_value(self):
        """Test setting payload values."""
        data = PipelineData.create(payload={"name": "Frank"})
        data.set_payload_value("age", 25)

        assert data.payload["age"] == 25

    def test_add_metadata(self):
        """Test adding metadata."""
        data = PipelineData.create(payload={})
        data.add_metadata("processor", "test-processor")
        data.add_metadata("timestamp", "2024-01-01")

        assert data.metadata["processor"] == "test-processor"
        assert data.metadata["timestamp"] == "2024-01-01"


class TestProcessingContext:
    """Test ProcessingContext class."""

    def test_initial_state(self):
        """Test initial context state."""
        data = PipelineData.create(payload={"test": "data"})
        context = ProcessingContext(data=data, state={})

        assert context.result == ProcessingResult.SUCCESS
        assert context.error is None
        assert context.processing_history == []

    def test_mark_success(self):
        """Test marking context as successful."""
        data = PipelineData.create(payload={})
        context = ProcessingContext(data=data, state={})
        context.mark_failure(Exception("test"))

        context.mark_success()

        assert context.result == ProcessingResult.SUCCESS
        assert context.error is None

    def test_mark_failure(self):
        """Test marking context as failed."""
        data = PipelineData.create(payload={})
        context = ProcessingContext(data=data, state={})
        error = ValueError("Test error")

        context.mark_failure(error)

        assert context.result == ProcessingResult.FAILURE
        assert context.error == error

    def test_mark_skip(self):
        """Test marking context as skipped."""
        data = PipelineData.create(payload={})
        context = ProcessingContext(data=data, state={})

        context.mark_skip()

        assert context.result == ProcessingResult.SKIP

    def test_add_to_history(self):
        """Test adding to processing history."""
        data = PipelineData.create(payload={})
        context = ProcessingContext(data=data, state={})

        context.add_to_history("Processor1")
        context.add_to_history("Processor2")

        assert context.processing_history == ["Processor1", "Processor2"]

    def test_status_checks(self):
        """Test status checking methods."""
        data = PipelineData.create(payload={})
        context = ProcessingContext(data=data, state={})

        assert context.is_success()
        assert not context.is_failure()
        assert not context.is_skip()

        context.mark_failure(Exception())
        assert not context.mark_skip()
        assert not context.is_success()
        assert not context.is_failure()
        assert context.is_skip()
