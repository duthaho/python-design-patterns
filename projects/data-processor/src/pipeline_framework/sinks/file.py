"""File-based data sinks."""

import csv
import json
from pathlib import Path
from typing import List, Optional

from pipeline_framework.adapters.base import DataAdapter
from pipeline_framework.adapters.csv_adapter import CSVAdapter
from pipeline_framework.adapters.json_adapter import JSONAdapter
from pipeline_framework.core.models import ProcessingContext
from pipeline_framework.sinks.base import Sink


class CSVFileSink(Sink):
    """
    Sink that writes results to CSV file.
    """

    def __init__(
        self,
        file_path: str,
        adapter: Optional[DataAdapter] = None,
        encoding: str = "utf-8",
        mode: str = "w",
        write_header: bool = True,
    ):
        """
        Initialize CSV file sink.

        Args:
            file_path: Path to output CSV file
            adapter: Data adapter (defaults to CSVAdapter)
            encoding: File encoding
            mode: File mode ('w' for write, 'a' for append)
            write_header: If True, write CSV header
        """
        self._file_path = Path(file_path)
        self._adapter = adapter or CSVAdapter()
        self._encoding = encoding
        self._mode = mode
        self._write_header = write_header
        self._closed = False
        self._writer = None
        self._file_handle = None
        self._headers_written = False

        # Create parent directory if it doesn't exist
        self._file_path.parent.mkdir(parents=True, exist_ok=True)

    def write(self, data: List[ProcessingContext]) -> None:
        """
        Write batch of results to CSV.

        Args:
            data: List of ProcessingContext objects to write
        """
        self._ensure_open()

        # Convert all contexts to rows first
        rows = [self._adapter.from_pipeline_data(context) for context in data]

        # Collect all unique fieldnames from all rows
        if self._writer is None:
            all_fieldnames = set()
            for row in rows:
                all_fieldnames.update(row.keys())

            # Create writer with all possible fields
            fieldnames = sorted(all_fieldnames)  # Sort for consistent column order
            self._writer = csv.DictWriter(
                self._file_handle,
                fieldnames=fieldnames,
                extrasaction="ignore",  # Ignore extra fields not in fieldnames
            )

            if self._write_header and not self._headers_written:
                self._writer.writeheader()
                self._headers_written = True

        # Write all rows
        for row in rows:
            self._writer.writerow(row)

    def write_single(self, context: ProcessingContext) -> None:
        """
        Write single result to CSV.

        Args:
            context: Single ProcessingContext to write
        """
        self.write([context])

    def close(self) -> None:
        """
        Close the file.
        """
        if not self._closed:
            if self._file_handle:
                self._file_handle.close()
                self._file_handle = None
            self._closed = True

    def _ensure_open(self) -> None:
        """
        Ensure file is open for writing.
        """
        if self._closed:
            raise RuntimeError("Cannot write to closed CSVFileSink")
        
        if self._file_handle is None:
            self._file_handle = self._file_path.open(
                mode=self._mode, encoding=self._encoding, newline=""
            )
            self._writer = None


class JSONFileSink(Sink):
    """
    Sink that writes results to JSON file.
    Supports both JSON array and JSON Lines formats.
    """

    def __init__(
        self,
        file_path: str,
        adapter: Optional[DataAdapter] = None,
        encoding: str = "utf-8",
        json_lines: bool = False,
        indent: Optional[int] = 2,
    ):
        """
        Initialize JSON file sink.

        Args:
            file_path: Path to output JSON file
            adapter: Data adapter (defaults to JSONAdapter)
            encoding: File encoding
            json_lines: If True, write JSON Lines format
            indent: Indentation for pretty printing (None for compact)
        """
        self._file_path = Path(file_path)
        self._file_handle = None
        self._first_write = True
        self._adapter = adapter or JSONAdapter()
        self._encoding = encoding
        self._json_lines = json_lines
        self._indent = indent
        self._closed = False
        self._results: List[dict] = []

        # Create parent directory
        self._file_path.parent.mkdir(parents=True, exist_ok=True)

    def write(self, data: List[ProcessingContext]) -> None:
        """
        Write batch of results.

        Args:
            data: List of ProcessingContext objects to write
        """
        if self._closed:
            raise RuntimeError("Cannot write to closed JSONFileSink")

        if self._json_lines:
            # Open file on first write, keep open for subsequent writes
            if self._file_handle is None:
                mode = "w" if self._first_write else "a"
                self._file_handle = self._file_path.open(mode=mode, encoding=self._encoding)
                self._first_write = False

            for context in data:
                obj = self._adapter.from_pipeline_data(context)
                # ✅ JSON Lines should have NO indentation (one object per line)
                line = json.dumps(obj, separators=(',', ':'))  # Compact format
                self._file_handle.write(line + "\n")

            # Flush to ensure data is written
            self._file_handle.flush()
        else:
            for context in data:
                obj = self._adapter.from_pipeline_data(context)
                self._results.append(obj)

    def write_single(self, context: ProcessingContext) -> None:
        """
        Write single result.

        Args:
            context: Single ProcessingContext to write
        """
        self.write([context])

    def close(self) -> None:
        """
        Close the sink and write final data.
        """
        if not self._closed:
            # Close JSON Lines file handle if open
            if self._file_handle:
                self._file_handle.close()
                self._file_handle = None

            # Write JSON array format
            if not self._json_lines and self._results:
                with self._file_path.open(mode="w", encoding=self._encoding) as f:
                    json.dump(self._results, f, indent=self._indent)
                self._results = []

            self._closed = True
