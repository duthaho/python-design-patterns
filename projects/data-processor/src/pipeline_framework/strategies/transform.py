"""Transformation strategies (Strategy pattern)."""

from abc import ABC, abstractmethod
from typing import Any, Callable, Dict

from pipeline_framework.core.models import PipelineData


class TransformStrategy(ABC):
    """
    Strategy interface for data transformation.
    This demonstrates the Strategy pattern.
    """

    @abstractmethod
    def transform(self, data: PipelineData, state: Dict[str, Any]) -> PipelineData:
        """
        Transform the data.

        Args:
            data: Data to transform
            state: Shared state (read-only recommended)

        Returns:
            Transformed data
        """
        pass


class UpperCaseTransform(TransformStrategy):
    """
    Transform all string values in payload to uppercase.

    Requirements:
    - Iterate through all payload items
    - Convert string values to uppercase
    - Keep non-string values unchanged
    - Return the modified data
    """

    def transform(self, data: PipelineData, state: Dict[str, Any]) -> PipelineData:
        """
        Transform string values in payload to uppercase.

        Example:
            Input:  {"name": "alice", "age": 30, "city": "NYC"}
            Output: {"name": "ALICE", "age": 30, "city": "NYC"}
        """
        cloned = data.clone()
        for key, value in cloned.payload.items():
            if isinstance(value, str):
                cloned.payload[key] = value.upper()
        return cloned


class LowerCaseTransform(TransformStrategy):
    """
    Transform all string values in payload to lowercase.
    """

    def transform(self, data: PipelineData, state: Dict[str, Any]) -> PipelineData:
        """
        Transform string values in payload to lowercase.

        Example:
            Input:  {"name": "ALICE", "age": 30, "city": "NYC"}
            Output: {"name": "alice", "age": 30, "city": "nyc"}
        """
        cloned = data.clone()
        for key, value in cloned.payload.items():
            if isinstance(value, str):
                cloned.payload[key] = value.lower()
        return cloned


class FilterFieldsTransform(TransformStrategy):
    """
    Filter payload to only include specified fields.
    """

    def __init__(self, fields: list[str]):
        """
        Initialize with fields to keep.

        Args:
            fields: List of field names to keep in payload
        """
        self._fields = fields

    def transform(self, data: PipelineData, state: Dict[str, Any]) -> PipelineData:
        """
        Filter payload to only include specified fields.

        Example:
            Fields: ["name", "city"]
            Input:  {"name": "alice", "age": 30, "city": "NYC"}
            Output: {"name": "alice", "city": "NYC"}
        """
        cloned = data.clone()
        cloned.payload = {k: v for k, v in cloned.payload.items() if k in self._fields}
        return cloned


class CustomFunctionTransform(TransformStrategy):
    """
    Apply a custom function to transform data.
    Demonstrates Strategy pattern with function injection.
    """

    def __init__(self, transform_func: Callable[[Dict[str, Any]], Dict[str, Any]]):
        """
        Initialize with a custom transform function.

        Args:
            transform_func: Function that takes a dict and returns a transformed dict
        """
        self._transform_func = transform_func

    def transform(self, data: PipelineData, state: Dict[str, Any]) -> PipelineData:
        """
        Apply the custom transform function to the payload.

        Example:
            Function: lambda p: {k: v*2 if isinstance(v, int) else v for k, v in p.items()}
            Input:  {"name": "alice", "age": 30}
            Output: {"name": "alice", "age": 60}
        """
        cloned = data.clone()
        cloned.payload = self._transform_func(cloned.payload)
        return cloned
