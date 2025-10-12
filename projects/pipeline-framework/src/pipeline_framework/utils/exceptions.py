"""Custom exceptions for the pipeline framework."""


class PipelineException(Exception):
    """Base exception for all pipeline errors."""

    pass


class TaskExecutionError(PipelineException):
    """Raised when a task fails during execution."""

    def __init__(self, task_name: str, original_error: Exception):
        self.task_name = task_name
        self.original_error = original_error
        super().__init__(f"Task '{task_name}' failed: {original_error}")


class ContextKeyError(PipelineException):
    """Raised when attempting to access a non-existent context key."""

    pass
