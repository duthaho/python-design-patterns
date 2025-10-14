"""State storage strategies (Strategy pattern)."""

import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict

from pipeline_framework.utils.exceptions import StateException


class StateStorage(ABC):
    """
    Strategy interface for state persistence.
    This demonstrates the Strategy pattern for storage backends.
    """

    @abstractmethod
    def load(self, pipeline_id: str) -> Dict[str, Any]:
        """
        Load state for a pipeline.

        Args:
            pipeline_id: Unique identifier for the pipeline

        Returns:
            State dictionary (empty dict if no state exists)
        """
        pass

    @abstractmethod
    def save(self, pipeline_id: str, state: Dict[str, Any]) -> None:
        """
        Save state for a pipeline.

        Args:
            pipeline_id: Unique identifier for the pipeline
            state: State dictionary to save
        """
        pass

    @abstractmethod
    def clear(self, pipeline_id: str) -> None:
        """
        Clear state for a pipeline.

        Args:
            pipeline_id: Unique identifier for the pipeline
        """
        pass

    @abstractmethod
    def exists(self, pipeline_id: str) -> bool:
        """
        Check if state exists for a pipeline.

        Args:
            pipeline_id: Unique identifier for the pipeline

        Returns:
            True if state exists, False otherwise
        """
        pass


class InMemoryStateStorage(StateStorage):
    """
    In-memory state storage (default implementation).
    State is lost when the process ends.
    """

    def __init__(self) -> None:
        """Initialize empty storage."""
        self._storage: Dict[str, Dict[str, Any]] = {}

    def load(self, pipeline_id: str) -> Dict[str, Any]:
        """
        Load state for a pipeline.

        Returns empty dict if no state exists.

        Args:
            pipeline_id: Unique identifier for the pipeline

        Returns:
            State dictionary (empty if none)
        """
        return self._storage.get(pipeline_id, {})

    def save(self, pipeline_id: str, state: Dict[str, Any]) -> None:
        """
        Save state for a pipeline.

        Args:
            pipeline_id: Unique identifier for the pipeline
            state: State dictionary to save
        """
        self._storage[pipeline_id] = state

    def clear(self, pipeline_id: str) -> None:
        """
        Clear state for a pipeline.

        Args:
            pipeline_id: Unique identifier for the pipeline
        """
        self._storage.pop(pipeline_id, None)

    def exists(self, pipeline_id: str) -> bool:
        """
        Check if state exists for a pipeline.

        Args:
            pipeline_id: Unique identifier for the pipeline

        Returns:
            True if state exists, False otherwise
        """
        return pipeline_id in self._storage


class FileStateStorage(StateStorage):
    """
    File-based state storage using JSON.
    State persists between process restarts.
    """

    def __init__(self, storage_dir: str = ".pipeline_state") -> None:
        """
        Initialize file storage.

        Args:
            storage_dir: Directory to store state files
        """
        self._storage_dir = Path(storage_dir)
        self._storage_dir.mkdir(exist_ok=True)

    def _get_state_file(self, pipeline_id: str) -> Path:
        """Get the path to the state file for a pipeline."""
        return self._storage_dir / f"{pipeline_id}.json"

    def load(self, pipeline_id: str) -> Dict[str, Any]:
        """
        Load state for a pipeline.
        Returns empty dict if no state exists.

        Args:
            pipeline_id: Unique identifier for the pipeline

        Returns:
            State dictionary (empty if none)
        """
        try:
            state_file = self._get_state_file(pipeline_id)
            if not state_file.exists():
                return {}
            with state_file.open("r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            raise StateException(f"Error loading state for pipeline {pipeline_id}: {e}")

    def save(self, pipeline_id: str, state: Dict[str, Any]) -> None:
        """
        Save state for a pipeline.

        Args:
            pipeline_id: Unique identifier for the pipeline
            state: State dictionary to save
        """
        try:
            state_file = self._get_state_file(pipeline_id)
            with state_file.open("w", encoding="utf-8") as f:
                json.dump(state, f, indent=4)
        except IOError as e:
            raise StateException(f"Error saving state for pipeline {pipeline_id}: {e}")

    def clear(self, pipeline_id: str) -> None:
        """
        Clear state for a pipeline.

        Args:
            pipeline_id: Unique identifier for the pipeline
        """
        try:
            state_file = self._get_state_file(pipeline_id)
            if state_file.exists():
                state_file.unlink(missing_ok=True)
        except IOError as e:
            raise StateException(f"Error clearing state for pipeline {pipeline_id}: {e}")

    def exists(self, pipeline_id: str) -> bool:
        """
        Check if state exists for a pipeline.

        Args:
            pipeline_id: Unique identifier for the pipeline

        Returns:
            True if state exists, False otherwise
        """
        state_file = self._get_state_file(pipeline_id)
        return state_file.exists()
