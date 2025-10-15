"""Tests for SourceFactory."""

import pytest
from pipeline_framework.core.models import PipelineData
from pipeline_framework.sources.factory import (SourceConfigBuilder,
                                                SourceFactory)
from pipeline_framework.sources.file import CSVFileSource
from pipeline_framework.sources.memory import MemorySource


class TestSourceFactory:
    """Test SourceFactory."""

    def test_create_memory_source(self):
        """Test creating memory source."""
        data = [PipelineData.create(payload={"value": 1})]
        source = SourceFactory.create("memory", data)

        assert isinstance(source, MemorySource)
        result = source.read()
        assert len(result) == 1

    def test_create_csv_file_source(self, tmp_path):
        """Test creating CSV file source."""
        import csv

        csv_file = tmp_path / "test.csv"
        with open(csv_file, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["id", "name"])
            writer.writeheader()
            writer.writerow({"id": "1", "name": "Alice"})

        source = SourceFactory.create("csv_file", str(csv_file))

        assert isinstance(source, CSVFileSource)
        result = source.read()
        assert len(result) == 1

    def test_create_from_config_csv(self, tmp_path):
        """Test creating source from config."""
        import csv

        csv_file = tmp_path / "test.csv"
        with open(csv_file, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["user_id", "name"])
            writer.writeheader()
            writer.writerow({"user_id": "123", "name": "Bob"})

        config = {
            "type": "csv_file",
            "file_path": str(csv_file),
            "adapter": {"id_field": "user_id"},
        }

        source = SourceFactory.create_from_config(config)
        result = source.read()

        assert result[0].id == "123"

    def test_create_from_config_json_lines(self, tmp_path):
        """Test creating JSON Lines source from config."""
        json_file = tmp_path / "test.jsonl"
        with open(json_file, "w") as f:
            f.write('{"id": "1", "name": "Alice"}\n')
            f.write('{"id": "2", "name": "Bob"}\n')

        config = {"type": "json_file", "file_path": str(json_file), "json_lines": True}

        source = SourceFactory.create_from_config(config)
        result = source.read()

        assert len(result) == 2

    def test_invalid_source_type_raises_error(self):
        """Test that invalid source type raises error."""
        with pytest.raises(ValueError, match="Unknown source type"):
            SourceFactory.create("nonexistent_type")

    def test_missing_required_config_raises_error(self):
        """Test that missing required config raises error."""
        with pytest.raises(TypeError):
            SourceFactory.create_from_config({"type": "csv_file"})  # Missing path

    def test_register_custom_source_type(self):
        """Test registering custom source type."""
        from pipeline_framework.sources.base import BatchSource

        class CustomSource(BatchSource):
            def __init__(self):
                pass

            def read(self):
                return []

            def close(self):
                pass

        SourceFactory.register_source_type("custom", CustomSource)

        assert "custom" in SourceFactory.list_available_types()

        source = SourceFactory.create("custom")
        assert isinstance(source, CustomSource)

    def test_list_available_types(self):
        """Test listing available source types."""
        types = SourceFactory.list_available_types()

        assert "memory" in types
        assert "csv_file" in types
        assert "json_file" in types
        assert len(types) >= 3


class TestSourceConfigBuilder:
    """Test SourceConfigBuilder."""

    def test_build_csv_config(self):
        """Test building CSV source config."""
        config = (
            SourceConfigBuilder("csv_file")
            .with_path("data.csv")
            .with_encoding("utf-8")
            .with_adapter(id_field="user_id", metadata_prefix="_m_")
            .build()
        )

        assert config["type"] == "csv_file"
        assert config["file_path"] == "data.csv"
        assert config["encoding"] == "utf-8"
        assert config["adapter"]["id_field"] == "user_id"

    def test_build_json_lines_config(self):
        """Test building JSON Lines config."""
        config = (
            SourceConfigBuilder("json_file").with_path("data.jsonl").with_json_lines(True).build()
        )

        assert config["json_lines"] is True

    def test_fluent_interface(self):
        """Test that methods return self for chaining."""
        builder = SourceConfigBuilder("csv_file")

        result = builder.with_path("test.csv")
        assert result is builder
