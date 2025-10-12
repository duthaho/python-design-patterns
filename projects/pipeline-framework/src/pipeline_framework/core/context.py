"""Pipeline context for sharing data between tasks."""

from typing import Any, Dict, Optional


class PipelineContext:
    """
    Shared data container for task communication.

    Tasks can read from and write to the context to pass data
    between pipeline stages.
    """

    def __init__(self, initial_data: Optional[Dict[str, Any]] = None):
        """
        Initialize context with optional initial data.

        Args:
            initial_data: Dictionary of initial key-value pairs
        """
        self._data: Dict[str, Any] = initial_data.copy() if initial_data else {}

    def set(self, key: str, value: Any) -> None:
        """
        Store a value in the context.

        Args:
            key: The key to store the value under
            value: The value to store
        """
        self._data[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        """
        Retrieve a value from the context.

        Args:
            key: The key to retrieve
            default: Default value if key doesn't exist

        Returns:
            The stored value or default
        """
        return self._data.get(key, default)

    def has(self, key: str) -> bool:
        """
        Check if a key exists in the context.

        Args:
            key: The key to check

        Returns:
            True if key exists, False otherwise
        """
        return key in self._data

    def get_all(self) -> Dict[str, Any]:
        """
        Get a copy of all context data.

        Returns:
            Dictionary containing all context data
        """
        return self._data.copy()
