"""
Pipeline Framework - A lightweight data processing framework for learning design patterns.
"""

__version__ = "0.1.0"

from .core.builder import PipelineBuilder
from .core.models import PipelineData, ProcessingContext, ProcessingResult
from .core.pipeline import Pipeline
from .core.processor import Processor
from .strategies.state import InMemoryStateStorage, StateStorage

__all__ = [
    "PipelineData",
    "ProcessingContext",
    "ProcessingResult",
    "Processor",
    "Pipeline",
    "PipelineBuilder",
    "StateStorage",
    "InMemoryStateStorage",
]