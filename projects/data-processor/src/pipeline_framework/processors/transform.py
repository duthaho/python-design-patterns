"""Transform processor that uses Strategy pattern."""

from pipeline_framework.core.models import ProcessingContext
from pipeline_framework.core.processor import Processor
from pipeline_framework.strategies.transform import TransformStrategy


class TransformProcessor(Processor):
    """
    Processor that applies a transformation strategy.
    Demonstrates how Strategy pattern integrates with Chain of Responsibility.
    """

    def __init__(self, strategy: TransformStrategy, name: str | None = None):
        """
        Initialize with a transformation strategy.

        Args:
            strategy: Transformation strategy to apply
            name: Optional processor name
        """
        super().__init__(name)
        self._strategy = strategy

    def _do_process(self, context: ProcessingContext) -> ProcessingContext:
        """Apply the transformation strategy to the data."""
        context.data = self._strategy.transform(context.data, context.state)
        return context
