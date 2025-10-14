"""Stateful processors that modify shared state."""

from pipeline_framework.core.models import ProcessingContext
from pipeline_framework.core.processor import Processor


class CounterProcessor(Processor):
    """
    Count processed items in shared state.
    Demonstrates stateful processing across multiple runs.
    """

    def __init__(self, counter_key: str = "processed_count", name: str | None = None):
        """
        Initialize counter processor.

        Args:
            counter_key: Key in state dict to store the count
            name: Optional processor name
        """
        super().__init__(name)
        self._counter_key = counter_key

    def _do_process(self, context: ProcessingContext) -> ProcessingContext:
        """Increment the counter in state."""
        counter = context.state.get(self._counter_key, 0)
        counter += 1
        context.state[self._counter_key] = counter
        return context


class DeduplicationProcessor(Processor):
    """
    Skip items that have been seen before (based on ID).
    Demonstrates stateful filtering.
    """

    def __init__(self, seen_ids_key: str = "seen_ids", name: str | None = None):
        """
        Initialize deduplication processor.

        Args:
            seen_ids_key: Key in state dict to store seen IDs
            name: Optional processor name
        """
        super().__init__(name)
        self._seen_ids_key = seen_ids_key

    def _do_process(self, context: ProcessingContext) -> ProcessingContext:
        """Skip processing if ID has been seen before."""
        seen_ids_list = context.state.get(self._seen_ids_key, [])
        seen_ids = set(seen_ids_list)

        if context.data.id in seen_ids:
            context.mark_skip()
        else:
            seen_ids.add(context.data.id)
            context.state[self._seen_ids_key] = list(seen_ids)

        return context


class AggregatorProcessor(Processor):
    """
    Aggregate values across all processed items.
    """

    def __init__(
        self, field: str, aggregation_key: str = "aggregated_values", name: str | None = None
    ):
        """
        Initialize aggregator processor.

        Args:
            field: Field in payload to aggregate
            aggregation_key: Key in state dict to store aggregated values
            name: Optional processor name
        """
        super().__init__(name)
        self._field = field
        self._aggregation_key = aggregation_key

    def _do_process(self, context: ProcessingContext) -> ProcessingContext:
        """Aggregate the specified field value into state."""
        aggregated_values = context.state.get(self._aggregation_key, [])
        value = context.data.payload.get(self._field)
        aggregated_values.append(value)
        context.state[self._aggregation_key] = aggregated_values
        return context
