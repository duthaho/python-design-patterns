"""Pipeline orchestrator."""

from typing import List, Optional

from pipeline_framework.core.models import (PipelineConfig, PipelineData,
                                            ProcessingContext)
from pipeline_framework.core.processor import Processor
from pipeline_framework.strategies.state import StateStorage
from pipeline_framework.utils.exceptions import PipelineException


class Pipeline:
    """
    Main pipeline orchestrator.
    Executes data through a chain of processors with state management.
    """

    def __init__(
        self,
        pipeline_id: str,
        processor_chain: Processor,
        state_storage: StateStorage,
        pipeline_config: Optional[PipelineConfig] = None,
    ):
        """
        Initialize pipeline.

        Args:
            pipeline_id: Unique identifier for this pipeline
            processor_chain: Head of the processor chain
            state_storage: State storage strategy
        """
        self.pipeline_id = pipeline_id
        self._config = pipeline_config or PipelineConfig()
        self._processor_chain = processor_chain
        self._state_storage = state_storage

    def execute(self, data_batch: List[PipelineData]) -> List[ProcessingContext]:
        """
        Execute pipeline on a batch of data.

        Args:
            data_batch: List of data items to process

        Returns:
            List of processing contexts (one per input item)
        """
        if not data_batch:
            return []

        state = self._state_storage.load(self.pipeline_id)

        results = []
        for data in data_batch:
            context = ProcessingContext(data=data, state=state, config=self._config)

            try:
                context = self._processor_chain.process(context)
            except Exception as e:
                raise PipelineException(f"Error processing data ID {data.id}") from e

            results.append(context)

        self._state_storage.save(self.pipeline_id, state)

        return results

    def execute_single(self, data: PipelineData) -> ProcessingContext:
        """
        Execute pipeline on a single data item.
        Convenience method that calls execute() with a single-item list.
        Args:
            data: Single data item to process

        Returns:
            Processing context for the input item
        """
        results = self.execute([data])
        return results[0] if results else None

    def get_state(self) -> dict:
        """Get current state from storage."""
        return self._state_storage.load(self.pipeline_id)

    def clear_state(self) -> None:
        """Clear state for this pipeline."""
        self._state_storage.clear(self.pipeline_id)
