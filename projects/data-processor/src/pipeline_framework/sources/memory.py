"""In-memory data sources."""

from typing import Any, Dict, Iterator, List

from pipeline_framework.core.models import PipelineData
from pipeline_framework.sources.base import BatchSource, StreamSource


class MemorySource(BatchSource):
    """
    Source that reads from an in-memory list of PipelineData.

    This is the simplest source - useful for testing and
    when you already have data loaded in memory.
    """

    def __init__(self, data: List[PipelineData]):
        """
        Initialize with pre-loaded data.

        Args:
            data: List of PipelineData objects
        """
        self._data = data
        self._closed = False

    def read(self) -> List[PipelineData]:
        """
        Return the in-memory data.

        Returns:
            List of PipelineData objects

        Raises:
            RuntimeError: If source is already closed
        """
        if self._closed:
            raise RuntimeError("Cannot read from closed MemorySource")
        return self._data.copy()

    def close(self) -> None:
        """
        Mark source as closed.
        """
        self._closed = True


class ListSource(BatchSource):
    """
    Source that converts a list of dictionaries to PipelineData.

    This is useful when you have raw data (like from an API)
    that needs to be converted to PipelineData format.
    """

    def __init__(self, data: List[Dict[str, Any]], id_field: str = "id"):
        """
        Initialize with raw dictionary data.

        Args:
            data: List of dictionaries (raw data)
            id_field: Field name to use as ID (or generate if missing)
        """
        self._raw_data = data
        self._id_field = id_field
        self._closed = False

    def read(self) -> List[PipelineData]:
        """
        Convert raw data to PipelineData objects.

        Returns:
            List of PipelineData objects
        """
        if self._closed:
            raise RuntimeError("Cannot read from closed ListSource")

        pipeline_data_list = []
        for item in self._raw_data:
            data_id = item.get(self._id_field)
            pipeline_data = PipelineData.create(payload=item, id=data_id)
            pipeline_data_list.append(pipeline_data)

        return pipeline_data_list

    def close(self) -> None:
        """Close the source."""
        self._closed = True


class MemoryStreamSource(StreamSource):
    """
    Streaming source that yields data one at a time from memory.

    Demonstrates the Iterator pattern even for in-memory data.
    Useful for testing streaming behavior.
    """

    def __init__(self, data: List[PipelineData]):
        """
        Initialize with data to stream.

        Args:
            data: List of PipelineData to yield one at a time
        """
        self._data = data
        self._closed = False

    def __iter__(self) -> Iterator[PipelineData]:
        """
        Yield data one item at a time.

        Yields:
            PipelineData objects one at a time

        Raises:
            RuntimeError: If source is closed
        """
        if self._closed:
            raise RuntimeError("Cannot iterate over closed MemoryStreamSource")

        for item in self._data:
            yield item

    def read(self) -> List[PipelineData]:
        """
        Read all data by consuming the iterator.

        Returns:
            List of PipelineData objects
        """
        return list(self)

    def close(self) -> None:
        """Close the source."""
        self._closed = True
