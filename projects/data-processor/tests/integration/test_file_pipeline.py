"""Integration tests for file-based pipelines."""

import csv
import json

from pipeline_framework import PipelineBuilder
from pipeline_framework.processors.stateful import CounterProcessor
from pipeline_framework.processors.transform import TransformProcessor
from pipeline_framework.sinks.file import CSVFileSink, JSONFileSink
from pipeline_framework.sources.file import CSVFileSource, JSONFileSource
from pipeline_framework.strategies.transform import UpperCaseTransform


class TestCSVPipeline:
    """Integration tests with CSV files."""

    def test_csv_to_csv_pipeline(self, tmp_path):
        """Test reading CSV, processing, and writing CSV."""
        # Create input CSV
        input_file = tmp_path / "input.csv"
        with open(input_file, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["id", "name", "city"])
            writer.writeheader()
            writer.writerow({"id": "1", "name": "alice", "city": "nyc"})
            writer.writerow({"id": "2", "name": "bob", "city": "sf"})

        output_file = tmp_path / "output.csv"

        # Create pipeline
        pipeline = (
            PipelineBuilder("csv-pipeline")
            .add_processor(TransformProcessor(UpperCaseTransform()))
            .add_processor(CounterProcessor())
            .build()
        )

        # Read, process, write
        source = CSVFileSource(str(input_file))
        data = source.read()
        source.close()

        results = pipeline.execute(data)

        sink = CSVFileSink(str(output_file))
        sink.write(results)
        sink.close()

        # Verify output
        with open(output_file, "r") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 2
            assert rows[0]["name"] == "ALICE"
            assert rows[1]["city"] == "SF"

    def test_csv_to_json_pipeline(self, tmp_path):
        """Test reading CSV and writing JSON."""
        # Create input CSV
        input_file = tmp_path / "input.csv"
        with open(input_file, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["id", "value"])
            writer.writeheader()
            writer.writerow({"id": "1", "value": "test"})

        output_file = tmp_path / "output.json"

        # Pipeline
        pipeline = PipelineBuilder("convert-pipeline").add_processor(CounterProcessor()).build()

        source = CSVFileSource(str(input_file))
        data = source.read()
        source.close()

        results = pipeline.execute(data)

        sink = JSONFileSink(str(output_file))
        sink.write(results)
        sink.close()

        assert output_file.exists()


class TestJSONPipeline:
    """Integration tests with JSON files."""

    def test_json_to_json_pipeline(self, tmp_path):
        """Test reading and writing JSON."""
        # Create input JSON
        input_file = tmp_path / "input.json"
        data = [
            {"id": "1", "name": "alice", "score": 85},
            {"id": "2", "name": "bob", "score": 90},
        ]
        with open(input_file, "w") as f:
            json.dump(data, f)

        output_file = tmp_path / "output.json"

        # Pipeline
        pipeline = (
            PipelineBuilder("json-pipeline")
            .add_processor(TransformProcessor(UpperCaseTransform()))
            .build()
        )

        source = JSONFileSource(str(input_file))
        data = source.read()
        source.close()

        results = pipeline.execute(data)

        sink = JSONFileSink(str(output_file))
        sink.write(results)
        sink.close()

        # Verify
        with open(output_file, "r") as f:
            output_data = json.load(f)
            assert len(output_data) == 2

    def test_json_lines_pipeline(self, tmp_path):
        """Test JSON Lines format."""
        # Create input
        input_file = tmp_path / "input.jsonl"
        with open(input_file, "w") as f:
            f.write('{"id": "1", "name": "alice"}\n')
            f.write('{"id": "2", "name": "bob"}\n')

        output_file = tmp_path / "output.jsonl"

        # Pipeline
        pipeline = PipelineBuilder("jsonl-pipeline").add_processor(CounterProcessor()).build()

        source = JSONFileSource(str(input_file), json_lines=True)
        data = source.read()
        source.close()

        results = pipeline.execute(data)

        sink = JSONFileSink(str(output_file), json_lines=True)
        sink.write(results)
        sink.close()

        # Verify
        with open(output_file, "r") as f:
            lines = f.readlines()
            assert len(lines) == 2


class TestLargeFilePipeline:
    """Test with larger datasets."""

    def test_stream_large_csv(self, tmp_path):
        """Test streaming large CSV file."""
        # Create large CSV
        input_file = tmp_path / "large.csv"
        with open(input_file, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["id", "value"])
            writer.writeheader()
            for i in range(10000):
                writer.writerow({"id": str(i), "value": f"item_{i}"})

        output_file = tmp_path / "output.csv"

        # Use streaming source
        from pipeline_framework.sources.file import CSVStreamSource

        pipeline = PipelineBuilder("stream-pipeline").add_processor(CounterProcessor()).build()

        source = CSVStreamSource(str(input_file))

        # Process in chunks
        sink = CSVFileSink(str(output_file))

        batch = []
        for item in source:
            batch.append(item)
            if len(batch) >= 100:
                results = pipeline.execute(batch)
                sink.write(results)
                batch = []

        # Process remaining
        if batch:
            results = pipeline.execute(batch)
            sink.write(results)

        source.close()
        sink.close()

        # Verify final state
        final_state = pipeline.get_state()
        assert final_state["processed_count"] == 10000
