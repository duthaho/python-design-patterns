"""Base adapter interface for data format conversion."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List

from pipeline_framework.core.models import PipelineData, ProcessingContext


class DataAdapter(ABC):
    """
    Abstract base class for data format adapters.
    Demonstrates the Adapter Pattern - converts between external formats
    and internal PipelineData representation.
    """

    @abstractmethod
    def to_pipeline_data(self, raw_data: Dict[str, Any]) -> PipelineData:
        """
        Convert raw data to PipelineData.

        Args:
            raw_data: Raw data in external format (e.g., CSV row, JSON object)

        Returns:
            PipelineData object

        Example:
            >>> adapter = CSVAdapter()
            >>> csv_row = {"id": "1", "name": "Alice", "age": "30"}
            >>> data = adapter.to_pipeline_data(csv_row)
        """
        pass

    @abstractmethod
    def from_pipeline_data(self, context: ProcessingContext) -> Dict[str, Any]:
        """
        Convert ProcessingContext back to raw data format.

        Args:
            context: ProcessingContext from pipeline execution

        Returns:
            Dictionary in external format

        Example:
            >>> adapter = CSVAdapter()
            >>> raw = adapter.from_pipeline_data(context)
            >>> # raw is ready to be written as CSV row
        """
        pass


class IdentityAdapter(DataAdapter):
    """
    Simple adapter that passes data through unchanged.
    Useful when data is already in correct format.
    """

    def to_pipeline_data(self, raw_data: Dict[str, Any]) -> PipelineData:
        """
        Convert dictionary to PipelineData.
        """
        return PipelineData.create(payload=raw_data)

    def from_pipeline_data(self, context: ProcessingContext) -> Dict[str, Any]:
        """
        Extract payload from context.
        """
        return context.data.payload
