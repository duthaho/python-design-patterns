"""Pipeline Framework - A framework for building data processing pipelines."""

__version__ = "0.1.0"

from .core.context import PipelineContext
from .core.pipeline import Pipeline
from .core.task import Task
from .utils.exceptions import (ContextKeyError, PipelineException,
                               TaskExecutionError)

__all__ = [
    "PipelineContext",
    "Pipeline",
    "Task",
    "PipelineException",
    "TaskExecutionError",
    "ContextKeyError",
]
