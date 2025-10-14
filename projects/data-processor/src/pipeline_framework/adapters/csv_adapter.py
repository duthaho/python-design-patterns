"""CSV data adapter."""

import uuid
from typing import Any, Dict

from pipeline_framework.adapters.base import DataAdapter
from pipeline_framework.core.models import PipelineData, ProcessingContext


class CSVAdapter(DataAdapter):
    """
    Adapter for CSV data format.
    Converts CSV rows (as dictionaries) to/from PipelineData.
    """

    def __init__(
        self,
        id_field: str = "id",
        include_metadata_fields: bool = False,
        metadata_prefix: str = "_meta_",
    ):
        """
        Initialize CSV adapter.

        Args:
            id_field: Field to use as ID
            include_metadata_fields: If True, include metadata in CSV output
            metadata_prefix: Prefix for metadata fields in CSV
        """
        self._id_field = id_field
        self._include_metadata = include_metadata_fields
        self._metadata_prefix = metadata_prefix

    def to_pipeline_data(self, raw_data: Dict[str, Any]) -> PipelineData:
        """
        Convert CSV row to PipelineData.

        Args:
            raw_data: Dictionary representing a CSV row

        Returns:
            PipelineData object

        Example:
            >>> adapter = CSVAdapter(id_field="user_id")
            >>> row = {"user_id": "123", "name": "Alice", "_meta_source": "api"}
            >>> data = adapter.to_pipeline_data(row)
            >>> # data.id == "123"
            >>> # data.payload == {"user_id": "123", "name": "Alice"}
            >>> # data.metadata == {"source": "api"}
        """
        if not isinstance(raw_data, dict):
            raise TypeError(f"Expected dict, got {type(raw_data)}")

        if not raw_data:
            raise ValueError("Cannot create PipelineData from empty dict")

        data_id = self._extract_id(raw_data)
        payload, metadata = self._separate_metadata(raw_data)
        return PipelineData.create(id=data_id, payload=payload, metadata=metadata)

    def from_pipeline_data(self, context: ProcessingContext) -> Dict[str, Any]:
        """
        Convert ProcessingContext to CSV row.

        Args:
            context: ProcessingContext to convert

        Returns:
            Dictionary ready to be written as CSV row

        Example:
            >>> adapter = CSVAdapter(include_metadata_fields=True)
            >>> row = adapter.from_pipeline_data(context)
            >>> # row includes payload + metadata with "_meta_" prefix
        """
        payload = context.data.payload.copy()

        # Add metadata fields with prefix
        if self._include_metadata:
            for key, value in context.data.metadata.items():
                payload[f"{self._metadata_prefix}{key}"] = value

        # Add processing status as FLAT fields (not nested dict)
        payload["_status"] = context.result.value

        if context.error:
            payload["_error"] = str(context.error)

        # Convert history list to string
        if context.processing_history:
            payload["_history"] = " -> ".join(context.processing_history)

        return payload

    def _extract_id(self, raw_data: Dict[str, Any]) -> str:
        """
        Extract or generate ID from raw data.

        Args:
            raw_data: Raw data dictionary

        Returns:
            ID string
        """
        return str(raw_data.get(self._id_field) or uuid.uuid4())

    def _separate_metadata(self, raw_data: Dict[str, Any]) -> tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Separate payload and metadata fields.

        Args:
            raw_data: Raw data dictionary

        Returns:
            Tuple of (payload_dict, metadata_dict)
        """
        payload = {}
        metadata = {}
        for key, value in raw_data.items():
            if key.startswith(self._metadata_prefix):
                meta_key = key[len(self._metadata_prefix) :]
                metadata[meta_key] = value
            else:
                payload[key] = value
        return payload, metadata
