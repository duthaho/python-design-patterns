"""Base classes for data sources."""

from abc import ABC, abstractmethod
from typing import Iterator, List

from pipeline_framework.core.models import PipelineData


class Source(ABC):
    """
    Abstract base class for data sources.
    Defines the interface for reading data into the pipeline.
    """

    @abstractmethod
    def read(self) -> List[PipelineData]:
        """
        Read all data from the source.

        Returns:
            List of PipelineData objects

        Note:
            For large datasets, consider using StreamSource instead.
        """
        pass

    @abstractmethod
    def close(self) -> None:
        """
        Close the source and release resources.
        Should be called after reading is complete.
        """
        pass

    def __enter__(self) -> "Source":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit - ensures cleanup."""
        self.close()


class BatchSource(Source):
    """
    Source that reads all data at once into memory.
    Suitable for small to medium datasets.
    """

    @abstractmethod
    def read(self) -> List[PipelineData]:
        """Read all data at once."""
        pass


class StreamSource(Source):
    """
    Source that reads data incrementally using iterator pattern.
    Suitable for large datasets that don't fit in memory.
    """

    @abstractmethod
    def __iter__(self) -> Iterator[PipelineData]:
        """
        Return an iterator over the data.

        Yields:
            PipelineData objects one at a time

        Example:
            >>> source = FileStreamSource("large_file.csv")
            >>> for data in source:
            ...     process(data)
        """
        pass

    def read(self) -> List[PipelineData]:
        """
        Read all data by consuming the iterator.

        Warning:
            This loads all data into memory. For large datasets,
            iterate directly instead of calling read().
        """
        return list(self)


class SourceConfig:
    """
    Configuration for creating sources.
    Used by SourceFactory.
    """

    pass
