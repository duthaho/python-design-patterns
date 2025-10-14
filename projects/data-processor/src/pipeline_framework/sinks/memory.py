"""In-memory data sinks."""

from typing import List

from pipeline_framework.core.models import ProcessingContext
from pipeline_framework.sinks.base import Sink


class MemorySink(Sink):
    """
    Sink that stores results in memory.

    Useful for testing and when you need to inspect results
    programmatically rather than writing to external storage.
    """

    def __init__(self):
        """Initialize empty results list."""
        self._results: List[ProcessingContext] = []
        self._closed = False

    def write(self, data: List[ProcessingContext]) -> None:
        """
        Write batch of results to memory.

        Args:
            data: List of ProcessingContext objects to store

        Raises:
            RuntimeError: If sink is closed
        """
        if self._closed:
            raise RuntimeError("Cannot write to closed MemorySink")
        self._results.extend(data)

    def write_single(self, context: ProcessingContext) -> None:
        """
        Write single result to memory.

        Args:
            context: Single ProcessingContext to store
        """
        if self._closed:
            raise RuntimeError("Cannot write to closed MemorySink")
        self._results.append(context)

    def get_results(self) -> List[ProcessingContext]:
        """
        Get all stored results.

        Returns:
            List of all ProcessingContext objects written to this sink
        """
        return self._results

    def close(self) -> None:
        """
        Close the sink.
        """
        self._closed = True


class ConsoleSink(Sink):
    """
    Sink that prints results to console.

    Useful for debugging and demos.
    """

    def __init__(self, verbose: bool = False):
        """
        Initialize console sink.

        Args:
            verbose: If True, print full context. If False, print summary.
        """
        self._verbose = verbose
        self._closed = False
        self._count = 0

    def write(self, data: List[ProcessingContext]) -> None:
        """
        Print batch of results to console.

        Args:
            data: List of ProcessingContext objects to print
        """
        if self._closed:
            raise RuntimeError("Cannot write to closed ConsoleSink")

        for context in data:
            self.write_single(context)

    def write_single(self, context: ProcessingContext) -> None:
        """
        Print single result to console.

        Args:
            context: Single ProcessingContext to print
        """
        if self._closed:
            raise RuntimeError("Cannot write to closed ConsoleSink")

        self._count += 1

        if self._verbose:
            print(f"\n{'='*60}")
            print(f"Context {self._count}")
            print(f"{'='*60}")
            print(f"  ID: {context.data.id}")
            print(f"  Status: {context.result.value}")
            print(f"  Payload: {context.data.payload}")
            print(f"  State: {context.state}")
            print(f"  History: {' -> '.join(context.processing_history)}")
            if context.error:
                print(f"  Error: {context.error}")
            print(f"{'='*60}\n")
        else:
            status = context.result.value.upper()
            error_msg = f", Error: {context.error}" if context.error else ""
            print(f"Context {self._count}: ID={context.data.id}, Status={status}{error_msg}")

    def close(self) -> None:
        """
        Close the sink and print summary.
        """
        if not self._closed:
            print(f"ConsoleSink closed. Total items written: {self._count}")
            self._closed = True
