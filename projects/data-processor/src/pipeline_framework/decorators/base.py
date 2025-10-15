"""Base decorator for processors."""

from typing import Optional

from pipeline_framework.core.models import ProcessingContext
from pipeline_framework.core.processor import Processor


class ProcessorDecorator(Processor):
    """
    Base decorator for adding behavior to processors.
    Implements the Decorator pattern.
    """

    def __init__(self, wrapped: Processor, name: Optional[str] = None):
        """
        Initialize decorator.

        Args:
            wrapped: The processor to wrap
            name: Optional name for this decorator
        """
        super().__init__(name or f"Decorated({wrapped.name})")
        self._wrapped = wrapped

    def _do_process(self, context: ProcessingContext) -> ProcessingContext:
        """
        Default implementation delegates to wrapped processor.
        Override in subclasses to add behavior.
        """
        return self._wrapped._do_process(context)

    @property
    def wrapped(self) -> Processor:
        """Get the wrapped processor."""
        return self._wrapped
