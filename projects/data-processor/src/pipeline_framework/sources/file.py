"""File-based data sources."""

import csv
import json
from pathlib import Path
from typing import Iterator, List, Optional

from pipeline_framework.adapters.base import DataAdapter
from pipeline_framework.adapters.csv_adapter import CSVAdapter
from pipeline_framework.adapters.json_adapter import JSONAdapter
from pipeline_framework.core.models import PipelineData
from pipeline_framework.sources.base import BatchSource, StreamSource


class CSVFileSource(BatchSource):
    """
    Source that reads CSV files.
    Uses CSVAdapter to convert rows to PipelineData.
    """

    def __init__(
        self,
        file_path: str,
        adapter: Optional[DataAdapter] = None,
        encoding: str = "utf-8",
    ):
        """
        Initialize CSV file source.

        Args:
            file_path: Path to CSV file
            adapter: Data adapter (defaults to CSVAdapter)
            encoding: File encoding
        """
        self._file_path = Path(file_path)
        self._adapter = adapter or CSVAdapter()
        self._encoding = encoding
        self._closed = False

        # Validate file exists
        if not self._file_path.exists():
            raise FileNotFoundError(f"CSV file not found: {file_path}")

    def read(self) -> List[PipelineData]:
        """
        Read all data from CSV file.

        Returns:
            List of PipelineData objects

        Raises:
            RuntimeError: If source is closed
            ValueError: If CSV is malformed
        """
        if self._closed:
            raise RuntimeError("Cannot read from closed CSVFileSource")

        results = []
        try:
            with self._file_path.open(mode="r", encoding=self._encoding) as f:
                reader = csv.DictReader(f)
                for row_num, row in enumerate(reader, start=2):  # Start at 2 (header is row 1)
                    try:
                        data = self._adapter.to_pipeline_data(row)
                        results.append(data)
                    except Exception as e:
                        # ✅ Add context about which row failed
                        raise ValueError(f"Error processing row {row_num}: {e}") from e
        except csv.Error as e:
            raise ValueError(f"Error reading CSV file: {e}")

        return results

    def close(self) -> None:
        """Close the source."""
        self._closed = True


class JSONFileSource(BatchSource):
    """
    Source that reads JSON files.
    Supports both JSON array and JSON Lines formats.
    """

    def __init__(
        self,
        file_path: str,
        adapter: Optional[DataAdapter] = None,
        encoding: str = "utf-8",
        json_lines: bool = False,
    ):
        """
        Initialize JSON file source.

        Args:
            file_path: Path to JSON file
            adapter: Data adapter (defaults to JSONAdapter)
            encoding: File encoding
            json_lines: If True, expect JSON Lines format (one object per line)
                       If False, expect JSON array format
        """
        self._file_path = Path(file_path)
        self._adapter = adapter or JSONAdapter()
        self._encoding = encoding
        self._json_lines = json_lines
        self._closed = False

        if not self._file_path.exists():
            raise FileNotFoundError(f"JSON file not found: {file_path}")

    def read(self) -> List[PipelineData]:
        """
        Read all data from JSON file.

        Returns:
            List of PipelineData objects
        """
        if self._closed:
            raise RuntimeError("Cannot read from closed JSONFileSource")

        results = []
        try:
            with self._file_path.open(mode="r", encoding=self._encoding) as f:
                if self._json_lines:
                    for line in f:
                        line = line.strip()
                        if line:
                            obj = json.loads(line)
                            data = self._adapter.to_pipeline_data(obj)
                            results.append(data)
                else:
                    content = f.read()
                    objs = json.loads(content)
                    if not isinstance(objs, list):
                        raise ValueError("Expected JSON array in file")
                    for obj in objs:
                        data = self._adapter.to_pipeline_data(obj)
                        results.append(data)
        except json.JSONDecodeError as e:
            raise ValueError(f"Error parsing JSON file: {e}")

        return results

    def close(self) -> None:
        """Close the source."""
        self._closed = True


class CSVStreamSource(StreamSource):
    """
    Streaming source for large CSV files.
    Yields one row at a time without loading entire file.

    This demonstrates the Iterator pattern for memory-efficient processing.
    """

    def __init__(
        self,
        file_path: str,
        adapter: Optional[DataAdapter] = None,
        encoding: str = "utf-8",
        chunk_size: int = 1000,
    ):
        """
        Initialize CSV stream source.

        Args:
            file_path: Path to CSV file
            adapter: Data adapter
            encoding: File encoding
            chunk_size: Number of rows to buffer (for efficiency)
        """
        self._file_path = Path(file_path)
        self._adapter = adapter or CSVAdapter()
        self._encoding = encoding
        self._chunk_size = chunk_size
        self._closed = False

        if not self._file_path.exists():
            raise FileNotFoundError(f"CSV file not found: {file_path}")

    def __iter__(self) -> Iterator[PipelineData]:
        """
        Iterate over CSV file, yielding one PipelineData at a time.

        Yields:
            PipelineData objects one at a time

        Note:
            This is memory-efficient for large files since we don't
            load the entire file into memory.
        """
        if self._closed:
            raise RuntimeError("Cannot iterate over closed CSVStreamSource")

        with self._file_path.open(mode="r", encoding=self._encoding) as f:
            reader = csv.DictReader(f)
            for row in reader:
                data = self._adapter.to_pipeline_data(row)
                yield data

    def close(self) -> None:
        """Close the source."""
        self._closed = True
