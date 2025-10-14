"""Tests for strategy implementations."""

import shutil
import tempfile
from pathlib import Path

import pytest
from pipeline_framework.core.models import PipelineData
from pipeline_framework.strategies.state import (FileStateStorage,
                                                 InMemoryStateStorage)
from pipeline_framework.strategies.transform import (CustomFunctionTransform,
                                                     FilterFieldsTransform,
                                                     LowerCaseTransform,
                                                     UpperCaseTransform)


class TestTransformStrategies:
    """Test transformation strategies."""

    def test_uppercase_transform(self):
        """Test uppercase transformation."""
        strategy = UpperCaseTransform()
        data = PipelineData.create(
            payload={"name": "alice", "city": "new york", "age": 30, "active": True}
        )

        result = strategy.transform(data, {})

        assert result.payload["name"] == "ALICE"
        assert result.payload["city"] == "NEW YORK"
        assert result.payload["age"] == 30  # Non-string unchanged
        assert result.payload["active"] is True  # Non-string unchanged

    def test_lowercase_transform(self):
        """Test lowercase transformation."""
        strategy = LowerCaseTransform()
        data = PipelineData.create(payload={"name": "ALICE", "city": "NEW YORK", "count": 100})

        result = strategy.transform(data, {})

        assert result.payload["name"] == "alice"
        assert result.payload["city"] == "new york"
        assert result.payload["count"] == 100

    def test_filter_fields_transform(self):
        """Test field filtering."""
        strategy = FilterFieldsTransform(fields=["name", "age"])
        data = PipelineData.create(
            payload={"name": "Bob", "age": 25, "city": "Boston", "country": "USA"}
        )

        result = strategy.transform(data, {})

        assert "name" in result.payload
        assert "age" in result.payload
        assert "city" not in result.payload
        assert "country" not in result.payload
        assert len(result.payload) == 2

    def test_custom_function_transform(self):
        """Test custom function transformation."""

        def double_numbers(payload):
            return {k: v * 2 if isinstance(v, (int, float)) else v for k, v in payload.items()}

        strategy = CustomFunctionTransform(double_numbers)
        data = PipelineData.create(payload={"price": 100, "quantity": 5, "name": "Product"})

        result = strategy.transform(data, {})

        assert result.payload["price"] == 200
        assert result.payload["quantity"] == 10
        assert result.payload["name"] == "Product"


class TestStateStorageStrategies:
    """Test state storage strategies."""

    def test_in_memory_storage_load_empty(self):
        """Test loading from empty in-memory storage."""
        storage = InMemoryStateStorage()
        state = storage.load("pipeline-1")

        assert state == {}

    def test_in_memory_storage_save_and_load(self):
        """Test saving and loading state."""
        storage = InMemoryStateStorage()
        test_state = {"count": 42, "last_id": "123"}

        storage.save("pipeline-1", test_state)
        loaded_state = storage.load("pipeline-1")

        assert loaded_state == test_state

    def test_in_memory_storage_multiple_pipelines(self):
        """Test isolated state for multiple pipelines."""
        storage = InMemoryStateStorage()

        storage.save("pipeline-1", {"value": 1})
        storage.save("pipeline-2", {"value": 2})

        assert storage.load("pipeline-1")["value"] == 1
        assert storage.load("pipeline-2")["value"] == 2

    def test_in_memory_storage_clear(self):
        """Test clearing state."""
        storage = InMemoryStateStorage()
        storage.save("pipeline-1", {"count": 10})

        storage.clear("pipeline-1")

        assert storage.load("pipeline-1") == {}

    def test_in_memory_storage_exists(self):
        """Test checking if state exists."""
        storage = InMemoryStateStorage()

        assert not storage.exists("pipeline-1")

        storage.save("pipeline-1", {"data": "test"})
        assert storage.exists("pipeline-1")

        storage.clear("pipeline-1")
        assert not storage.exists("pipeline-1")

    def test_file_storage_save_and_load(self):
        """Test file-based storage."""
        temp_dir = tempfile.mkdtemp()
        try:
            storage = FileStateStorage(storage_dir=temp_dir)
            test_state = {"count": 100, "items": ["a", "b", "c"]}

            storage.save("pipeline-1", test_state)
            loaded_state = storage.load("pipeline-1")

            assert loaded_state == test_state

            # Verify file was created
            state_file = Path(temp_dir) / "pipeline-1.json"
            assert state_file.exists()
        finally:
            shutil.rmtree(temp_dir)

    def test_file_storage_load_nonexistent(self):
        """Test loading from non-existent file."""
        temp_dir = tempfile.mkdtemp()
        try:
            storage = FileStateStorage(storage_dir=temp_dir)
            state = storage.load("nonexistent-pipeline")

            assert state == {}
        finally:
            shutil.rmtree(temp_dir)

    def test_file_storage_clear(self):
        """Test clearing file-based state."""
        temp_dir = tempfile.mkdtemp()
        try:
            storage = FileStateStorage(storage_dir=temp_dir)
            storage.save("pipeline-1", {"data": "test"})

            state_file = Path(temp_dir) / "pipeline-1.json"
            assert state_file.exists()

            storage.clear("pipeline-1")
            assert not state_file.exists()
        finally:
            shutil.rmtree(temp_dir)

    def test_file_storage_exists(self):
        """Test checking file existence."""
        temp_dir = tempfile.mkdtemp()
        try:
            storage = FileStateStorage(storage_dir=temp_dir)

            assert not storage.exists("pipeline-1")

            storage.save("pipeline-1", {"test": True})
            assert storage.exists("pipeline-1")
        finally:
            shutil.rmtree(temp_dir)

    def test_file_storage_persistence(self):
        """Test that file storage persists between instances."""
        temp_dir = tempfile.mkdtemp()
        try:
            # First instance saves data
            storage1 = FileStateStorage(storage_dir=temp_dir)
            storage1.save("pipeline-1", {"persisted": True, "value": 999})

            # Second instance (simulating restart) should load the data
            storage2 = FileStateStorage(storage_dir=temp_dir)
            loaded = storage2.load("pipeline-1")

            assert loaded == {"persisted": True, "value": 999}
        finally:
            shutil.rmtree(temp_dir)
