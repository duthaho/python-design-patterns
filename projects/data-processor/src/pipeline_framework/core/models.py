"""Core data models for the pipeline framework."""

import copy
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional


class ProcessingResult(Enum):
    """Result status of processing."""

    SUCCESS = "success"
    FAILURE = "failure"
    SKIP = "skip"


@dataclass(frozen=True)
class PipelineConfig:
    """Configuration for the pipeline."""

    stop_on_failure: bool = False
    stop_on_skip: bool = False


@dataclass
class PipelineData:
    """Data flowing through the pipeline."""

    id: str
    payload: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

    @classmethod
    def create(cls, payload: Dict[str, Any], **kwargs: Any) -> "PipelineData":
        """Factory method to create PipelineData with auto-generated ID."""
        return cls(
            id=kwargs.get("id", str(uuid.uuid4())),
            payload=payload,
            metadata=kwargs.get("metadata", {}),
            timestamp=kwargs.get("timestamp", datetime.now()),
        )

    def clone(self) -> "PipelineData":
        """
        Create a deep copy of this data.

        Returns:
            A new PipelineData instance with copied data
        """
        return PipelineData(
            id=self.id,
            payload=copy.deepcopy(self.payload),
            metadata=copy.deepcopy(self.metadata),
            timestamp=self.timestamp,
        )

    def get_payload_value(self, key: str, default: Any = None) -> Any:
        """Safely get a value from payload."""
        return self.payload.get(key, default)

    def set_payload_value(self, key: str, value: Any) -> None:
        """Set a value in payload."""
        self.payload[key] = value

    def add_metadata(self, key: str, value: Any) -> None:
        """Add metadata."""
        self.metadata[key] = value


@dataclass
class ProcessingContext:
    """Context passed through the processor chain."""

    data: PipelineData
    state: Dict[str, Any]
    config: PipelineConfig = field(default_factory=PipelineConfig)
    result: ProcessingResult = ProcessingResult.SUCCESS
    error: Optional[Exception] = None
    processing_history: list[str] = field(default_factory=list)

    def mark_success(self) -> None:
        """Mark processing as successful."""
        self.result = ProcessingResult.SUCCESS
        self.error = None

    def mark_failure(self, error: Exception) -> None:
        """Mark processing as failed."""
        self.result = ProcessingResult.FAILURE
        self.error = error

    def mark_skip(self) -> None:
        """Mark processing as skipped."""
        self.result = ProcessingResult.SKIP

    def add_to_history(self, processor_name: str) -> None:
        """Add processor to processing history."""
        self.processing_history.append(processor_name)

    def is_success(self) -> bool:
        """Check if processing was successful."""
        return self.result == ProcessingResult.SUCCESS

    def is_failure(self) -> bool:
        """Check if processing failed."""
        return self.result == ProcessingResult.FAILURE

    def is_skip(self) -> bool:
        """Check if processing was skipped."""
        return self.result == ProcessingResult.SKIP
