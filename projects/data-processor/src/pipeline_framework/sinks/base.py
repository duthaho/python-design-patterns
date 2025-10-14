"""Base classes for data sinks."""

from abc import ABC, abstractmethod
from typing import List

from pipeline_framework.core.models import ProcessingContext


class Sink(ABC):
    """
    Abstract base class for data sinks.
    Defines the interface for writing pipeline results.
    """

    @abstractmethod
    def write(self, data: List[ProcessingContext]) -> None:
        """
        Write processed data to the sink.

        Args:
            data: List of ProcessingContext objects from pipeline execution

        Note:
            Implementations should handle errors gracefully and
            provide meaningful error messages.
        """
        pass

    @abstractmethod
    def write_single(self, context: ProcessingContext) -> None:
        """
        Write a single ProcessingContext to the sink.

        Args:
            context: Single ProcessingContext to write

        Note:
            Useful for streaming writes during pipeline execution.
        """
        pass

    @abstractmethod
    def close(self) -> None:
        """
        Close the sink and flush any buffered data.

        Note:
            Should be called after all writing is complete.
            Should be idempotent (safe to call multiple times).
        """
        pass

    def __enter__(self) -> "Sink":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit - ensures cleanup."""
        self.close()


class SinkConfig:
    """
    Configuration for creating sinks.
    Used by SinkFactory.
    """

    pass
