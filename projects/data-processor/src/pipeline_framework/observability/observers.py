"""Concrete observer implementations."""

import json
from typing import Optional, TextIO

from pipeline_framework.observability.events import (EventType, Observer,
                                                     PipelineEvent)


class ConsoleObserver(Observer):
    """
    Observer that prints events to console.
    """

    def __init__(self, verbose: bool = False):
        """
        Initialize console observer.

        Args:
            verbose: If True, print detailed info. If False, print summary.
        """
        self._verbose = verbose

    def on_event(self, event: PipelineEvent) -> None:
        """
        Print event to console.
        """
        if self._verbose:
            print(
                f"[{event.timestamp.isoformat()}] Event: {event.event_type.value}, "
                f"Pipeline: {event.pipeline_id}, Data ID: {event.data.id if event.data else 'N/A'}, "
                f"Processor: {event.processor_name}, Error: {str(event.error) if event.error else 'None'}, "
                f"Metadata: {json.dumps(event.metadata)}"
            )
        else:
            if event.event_type in {
                EventType.PIPELINE_STARTED,
                EventType.PIPELINE_COMPLETED,
                EventType.PIPELINE_FAILED,
            }:
                print(
                    f"[{event.timestamp.isoformat()}] Event: {event.event_type.value}, "
                    f"Pipeline: {event.pipeline_id}, Error: {str(event.error) if event.error else 'None'}"
                )


class FileObserver(Observer):
    """
    Observer that writes events to a file.
    """

    def __init__(self, file_path: str, format: str = "json"):
        """
        Initialize file observer.

        Args:
            file_path: Path to log file
            format: Log format ('json' or 'text')
        """
        self._file_path = file_path
        self._format = format
        self._file: Optional[TextIO] = None

    def on_event(self, event: PipelineEvent) -> None:
        """
        Write event to file.

        Steps:
        1. Open file if not already open (append mode)
        2. Format event based on self._format
        3. Write to file
        4. Flush to ensure it's written
        """
        if self._file is None:
            self._file = open(self._file_path, "a", encoding="utf-8")

        if self._format == "json":
            line = json.dumps(event.to_dict())
        else:  # Plain text format
            line = (
                f"[{event.timestamp.isoformat()}] Event: {event.event_type.value}, "
                f"Pipeline: {event.pipeline_id}, Data ID: {event.data.id if event.data else 'N/A'}, "
                f"Processor: {event.processor_name}, Error: {str(event.error) if event.error else 'None'}, "
                f"Metadata: {json.dumps(event.metadata)}"
            )

        self._file.write(line + "\n")
        self._file.flush()

    def close(self) -> None:
        """
        Close the file.
        """
        if self._file:
            self._file.close()
            self._file = None

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
