"""Pipeline Framework - A framework for building data processing pipelines."""

__version__ = "0.1.0"

from .core.context import PipelineContext
from .core.pipeline import Pipeline
from .core.task import Task
from .events import (ConsoleListener, EventType, PipelineEvent,
                     PipelineListener, StatisticsListener)
from .factories import (FunctionTask, LogTask, SetValueTask, TaskFactory,
                        TaskRegistry)
from .utils.exceptions import (ContextKeyError, PipelineException,
                               TaskExecutionError)

__all__ = [
    # Core
    "PipelineContext",
    "Pipeline",
    "Task",
    # Events
    "EventType",
    "PipelineEvent",
    "PipelineListener",
    "ConsoleListener",
    "StatisticsListener",
    # Factory
    "TaskFactory",
    "TaskRegistry",
    "FunctionTask",
    "LogTask",
    "SetValueTask",
    # Exceptions
    "PipelineException",
    "TaskExecutionError",
    "ContextKeyError",
]
