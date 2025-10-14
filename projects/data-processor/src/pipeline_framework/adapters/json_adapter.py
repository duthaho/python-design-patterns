"""JSON data adapter."""

import uuid
from typing import Any, Dict

from pipeline_framework.adapters.base import DataAdapter
from pipeline_framework.core.models import PipelineData, ProcessingContext


class JSONAdapter(DataAdapter):
    """
    Adapter for JSON data format.
    Handles nested structures better than CSV.
    """

    def __init__(
        self,
        id_field: str = "id",
        include_processing_info: bool = False,
    ):
        """
        Initialize JSON adapter.

        Args:
            id_field: Field to use as ID
            include_processing_info: If True, include processing status in output
        """
        self._id_field = id_field
        self._include_processing_info = include_processing_info

    def to_pipeline_data(self, raw_data: Dict[str, Any]) -> PipelineData:
        """
        Convert JSON object to PipelineData.

        Args:
            raw_data: Dictionary representing a JSON object

        Returns:
            PipelineData object
        """
        data_id = str(raw_data.get(self._id_field) or uuid.uuid4())

        # Extract metadata, remove both metadata and id from payload
        metadata = raw_data.get("metadata", {})
        payload = {k: v for k, v in raw_data.items() if k not in ("metadata", self._id_field)}

        return PipelineData.create(id=data_id, payload=payload, metadata=metadata)

    def from_pipeline_data(self, context: ProcessingContext) -> Dict[str, Any]:
        """
        Convert ProcessingContext to JSON object.

        Args:
            context: ProcessingContext to convert

        Returns:
            Dictionary ready to be serialized as JSON
        """
        result = {
            "id": context.data.id,
            "payload": context.data.payload,
        }

        if context.data.metadata:
            result["metadata"] = context.data.metadata

        if self._include_processing_info:
            result["processing"] = {
                "status": context.result.value,
                "error": str(context.error) if context.error else None,
                "history": context.processing_history,
            }

        return result
