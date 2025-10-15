"""Tests for SinkFactory."""

import json

import pytest
from pipeline_framework.core.models import PipelineData, ProcessingContext
from pipeline_framework.sinks.factory import SinkConfigBuilder, SinkFactory
from pipeline_framework.sinks.file import CSVFileSink
from pipeline_framework.sinks.memory import ConsoleSink, MemorySink


class TestSinkFactory:
    """Test SinkFactory."""

    def test_create_memory_sink(self):
        """Test creating memory sink."""
        sink = SinkFactory.create("memory")

        assert isinstance(sink, MemorySink)

    def test_create_console_sink(self):
        """Test creating console sink."""
        sink = SinkFactory.create("console", verbose=True)

        assert isinstance(sink, ConsoleSink)

    def test_create_csv_file_sink(self, tmp_path):
        """Test creating CSV file sink."""
        csv_file = tmp_path / "output.csv"

        sink = SinkFactory.create("csv_file", str(csv_file))

        assert isinstance(sink, CSVFileSink)

    def test_create_from_config_json(self, tmp_path):
        """Test creating JSON sink from config."""
        json_file = tmp_path / "output.json"

        config = {
            "type": "json_file",
            "file_path": str(json_file),
            "indent": 4,
            "adapter": {"include_processing_info": True},
        }

        sink = SinkFactory.create_from_config(config)

        # Write test data
        context = ProcessingContext(data=PipelineData.create(payload={"test": "data"}), state={})
        sink.write([context])
        sink.close()

        # Verify file was created
        assert json_file.exists()

        with open(json_file, "r") as f:
            data = json.load(f)
            assert isinstance(data, list)

    def test_invalid_sink_type_raises_error(self):
        """Test invalid sink type."""
        with pytest.raises(ValueError, match="Unknown sink type"):
            SinkFactory.create("nonexistent_type")

    def test_register_custom_sink_type(self):
        """Test registering custom sink."""
        from pipeline_framework.sinks.base import Sink

        class CustomSink(Sink):
            def write(self, data):
                pass

            def write_single(self, context):
                pass

            def close(self):
                pass

        SinkFactory.register_sink_type("custom", CustomSink)

        assert "custom" in SinkFactory.list_available_types()

        sink = SinkFactory.create("custom")
        assert isinstance(sink, CustomSink)

    def test_list_available_types(self):
        """Test listing sink types."""
        types = SinkFactory.list_available_types()

        assert "memory" in types
        assert "console" in types
        assert "csv_file" in types
        assert "json_file" in types


class TestSinkConfigBuilder:
    """Test SinkConfigBuilder."""

    def test_build_csv_config(self):
        """Test building CSV sink config."""
        config = (
            SinkConfigBuilder("csv_file")
            .with_path("output.csv")
            .with_mode("w")
            .with_adapter(include_metadata_fields=True)
            .build()
        )

        assert config["type"] == "csv_file"
        assert config["file_path"] == "output.csv"
        assert config["mode"] == "w"

    def test_build_json_lines_config(self):
        """Test building JSON Lines sink config."""
        config = (
            SinkConfigBuilder("json_file").with_path("output.jsonl").with_json_lines(True).build()
        )

        assert config["json_lines"] is True
