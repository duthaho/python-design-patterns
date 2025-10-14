"""Base processor class implementing Chain of Responsibility and Template Method patterns."""

from abc import ABC, abstractmethod
from typing import Optional

from pipeline_framework.core.models import ProcessingContext, ProcessingResult


class Processor(ABC):
    """
    Base processor in the chain (Chain of Responsibility pattern).
    Uses Template Method pattern for processing flow.
    """

    def __init__(self, name: Optional[str] = None):
        """
        Initialize processor.

        Args:
            name: Optional name for the processor. If not provided, uses class name.
        """
        self._next: Optional[Processor] = None
        self._name = name or self.__class__.__name__

    @property
    def name(self) -> str:
        """Get processor name."""
        return self._name

    def set_next(self, processor: "Processor") -> "Processor":
        """
        Chain the next processor.

        Args:
            processor: Next processor in the chain

        Returns:
            The processor that was set (for chaining)

        Example:
            processor1.set_next(processor2).set_next(processor3)
        """
        self._next = processor
        return processor

    def process(self, context: ProcessingContext) -> ProcessingContext:
        """
        Template method - defines the processing flow.
        This is the Template Method pattern in action!

        Args:
            context: Processing context

        Returns:
            Updated processing context
        """
        context.add_to_history(self._name)

        if not self._should_process(context):
            return self._pass_to_next(context)

        try:
            context = self._do_process(context)
        except Exception as e:
            context = self._handle_error(context, e)
            if self._should_stop_on_failure(context):
                return context

        if self._should_stop_on_failure(context):
            return context
        
        return self._pass_to_next(context)

    @abstractmethod
    def _do_process(self, context: ProcessingContext) -> ProcessingContext:
        """
        Actual processing logic - subclasses MUST implement this.

        This is the core method where each processor does its work.

        Args:
            context: Processing context

        Returns:
            Updated processing context
        """
        pass

    def _should_process(self, context: ProcessingContext) -> bool:
        """
        Hook method - determine if this processor should run.
        Override in subclasses for conditional processing.

        Default behavior: Don't process if previous processor failed.

        Args:
            context: Processing context

        Returns:
            True if should process, False otherwise
        """
        return context.result == ProcessingResult.SUCCESS
    
    def _should_stop_on_failure(self, context: ProcessingContext) -> bool:
        """
        Hook method - determine if processing should stop on failure.
        Override in subclasses for custom behavior.

        Default behavior: Stop if config says to stop on failure.

        Args:
            context: Processing context

        Returns:
            True if should stop, False otherwise
        """
        return context.config.stop_on_failure and context.is_failure()
    
    def _should_stop_on_skip(self, context: ProcessingContext) -> bool:
        """
        Hook method - determine if processing should stop on skip.
        Override in subclasses for custom behavior.

        Default behavior: Stop if config says to stop on skip.

        Args:
            context: Processing context

        Returns:
            True if should stop, False otherwise
        """
        return context.config.stop_on_skip and context.is_skip()

    def _handle_error(self, context: ProcessingContext, error: Exception) -> ProcessingContext:
        """
        Hook method - handle errors during processing.
        Override in subclasses for custom error handling.

        Default behavior: Mark context as failed and store the error.

        Args:
            context: Processing context
            error: The exception that occurred

        Returns:
            Updated processing context
        """
        context.mark_failure(error)
        return context

    def _pass_to_next(self, context: ProcessingContext) -> ProcessingContext:
        """
        Pass context to the next processor in the chain.

        Args:
            context: Processing context

        Returns:
            Processing context (possibly modified by next processor)
        """
        if self._next:
            return self._next.process(context)
        return context

    def __repr__(self) -> str:
        """String representation of processor."""
        return f"{self.__class__.__name__}(name='{self._name}')"
