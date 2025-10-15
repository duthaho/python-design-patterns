"""Command pattern for pipeline operations."""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, List, Optional


class Command(ABC):
    """
    Abstract command interface.
    Implements the Command pattern for encapsulating operations.
    """

    def __init__(self):
        """Initialize command."""
        self._executed = False
        self._execution_time: Optional[datetime] = None
        self._result: Any = None

    @abstractmethod
    def execute(self) -> Any:
        """
        Execute the command.

        Returns:
            Command execution result
        """
        pass

    @abstractmethod
    def undo(self) -> None:
        """
        Undo the command.

        Note:
            Not all commands are undoable.
            Raise NotImplementedError if undo is not supported.
        """
        pass

    def can_undo(self) -> bool:
        """Check if command can be undone."""
        return self._executed

    @property
    def is_executed(self) -> bool:
        """Check if command has been executed."""
        return self._executed

    @property
    def execution_time(self) -> Optional[datetime]:
        """Get execution timestamp."""
        return self._execution_time

    @property
    def result(self) -> Any:
        """Get command result."""
        return self._result


class CommandHistory:
    """
    Maintains history of executed commands.
    Supports undo/redo operations.
    """

    def __init__(self, max_history: int = 100):
        """
        Initialize command history.

        Args:
            max_history: Maximum number of commands to keep in history
        """
        self._history: List[Command] = []
        self._current_index = -1
        self._max_history = max_history

    def execute(self, command: Command) -> Any:
        """
        Execute a command and add to history.

        Args:
            command: Command to execute

        Returns:
            Command execution result
        """
        result = command.execute()
        if self._current_index < len(self._history) - 1:
            self._history = self._history[: self._current_index + 1]
        self._history.append(command)
        if len(self._history) > self._max_history:
            self._history.pop(0)
        else:
            self._current_index += 1
        return result

    def undo(self) -> None:
        """
        Undo the last command.

        Raises:
            IndexError: If no commands to undo
        """
        if not self.can_undo():
            raise IndexError("No commands to undo")
        command = self._history[self._current_index]
        command.undo()
        self._current_index -= 1

    def redo(self) -> None:
        """
        Redo the last undone command.

        Raises:
            IndexError: If no commands to redo
        """
        if not self.can_redo():
            raise IndexError("No commands to redo")
        self._current_index += 1
        command = self._history[self._current_index]
        command.execute()

    def can_undo(self) -> bool:
        """Check if undo is possible."""
        return self._current_index >= 0

    def can_redo(self) -> bool:
        """Check if redo is possible."""
        return self._current_index < len(self._history) - 1

    def clear(self) -> None:
        """Clear command history."""
        self._history.clear()
        self._current_index = -1

    @property
    def history_size(self) -> int:
        """Get number of commands in history."""
        return len(self._history)
