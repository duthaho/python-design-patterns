"""Integration tests with factories."""

import csv
import json

from pipeline_framework import PipelineBuilder
from pipeline_framework.processors.stateful import CounterProcessor
from pipeline_framework.processors.transform import TransformProcessor
from pipeline_framework.sinks.factory import SinkFactory
from pipeline_framework.sources.factory import SourceFactory
from pipeline_framework.strategies.transform import UpperCaseTransform


class TestFactoryPipeline:
    """Test complete pipelines using factories."""

    def test_csv_to_json_with_factories(self, tmp_path):
        """Test CSV to JSON pipeline using factories."""
        # Create input CSV
        input_file = tmp_path / "input.csv"
        with open(input_file, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["id", "name", "value"])
            writer.writeheader()
            writer.writerow({"id": "1", "name": "alice", "value": "100"})
            writer.writerow({"id": "2", "name": "bob", "value": "200"})

        output_file = tmp_path / "output.json"

        # Create pipeline with factories
        source = SourceFactory.create("csv_file", str(input_file))
        sink = SinkFactory.create("json_file", str(output_file))

        pipeline = (
            PipelineBuilder("factory-pipeline")
            .add_processor(TransformProcessor(UpperCaseTransform()))
            .add_processor(CounterProcessor())
            .build()
        )

        # Execute
        data = source.read()
        source.close()

        results = pipeline.execute(data)

        sink.write(results)
        sink.close()

        # Verify
        with open(output_file, "r") as f:
            output_data = json.load(f)
            assert len(output_data) == 2
            assert output_data[0]["payload"]["name"] == "ALICE"

    def test_config_based_pipeline(self, tmp_path):
        """Test building pipeline from configuration."""
        # Create input
        input_file = tmp_path / "input.json"
        data = [{"id": "1", "value": "test"}]
        with open(input_file, "w") as f:
            json.dump(data, f)

        output_file = tmp_path / "output.json"

        # Configuration-driven pipeline
        source_config = {"type": "json_file", "file_path": str(input_file)}

        sink_config = {"type": "json_file", "file_path": str(output_file), "indent": 2}

        source = SourceFactory.create_from_config(source_config)
        sink = SinkFactory.create_from_config(sink_config)

        pipeline = PipelineBuilder("config-pipeline").add_processor(CounterProcessor()).build()

        # Execute
        data = source.read()
        results = pipeline.execute(data)
        sink.write(results)

        source.close()
        sink.close()

        assert output_file.exists()

    def test_builder_with_source_and_sink(self, tmp_path):
        """Test PipelineBuilder with integrated source/sink."""
        # Create input
        input_file = tmp_path / "input.csv"
        with open(input_file, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["id", "name"])
            writer.writeheader()
            writer.writerow({"id": "1", "name": "test"})

        output_file = tmp_path / "output.json"

        # Build and run in one go
        source = SourceFactory.create("csv_file", str(input_file))
        sink = SinkFactory.create("json_file", str(output_file))

        results = (
            PipelineBuilder("integrated-pipeline")
            .with_source(source)
            .add_processor(CounterProcessor())
            .with_sink(sink)
            .build_and_run()
        )

        assert len(results) == 1
        assert output_file.exists()

        # Verify output
        with open(output_file, "r") as f:
            output_data = json.load(f)
            assert len(output_data) == 1

    def test_builder_with_config_methods(self, tmp_path):
        """Test PipelineBuilder with config-based source/sink."""
        # Create input
        input_file = tmp_path / "input.jsonl"
        with open(input_file, "w") as f:
            f.write('{"id": "1", "name": "alice"}\n')
            f.write('{"id": "2", "name": "bob"}\n')

        output_file = tmp_path / "output.jsonl"

        # Use config methods
        results = (
            PipelineBuilder("config-based-pipeline")
            .with_source_config({"type": "json_file", "file_path": str(input_file), "json_lines": True})
            .add_processor(TransformProcessor(UpperCaseTransform()))
            .add_processor(CounterProcessor())
            .with_sink_config({"type": "json_file", "file_path": str(output_file), "json_lines": True})
            .build_and_run()
        )

        assert len(results) == 2
        assert results[-1].state["processed_count"] == 2

        # Verify output file
        with open(output_file, "r") as f:
            lines = f.readlines()
            assert len(lines) == 2

            obj = json.loads(lines[0])
            assert obj["payload"]["name"] == "ALICE"
